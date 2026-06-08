-- ================================================================
-- schema.sql — FixLoop AI  (Supabase / PostgreSQL)
-- ================================================================
-- This file is the consolidated schema for reference and CI.
-- The canonical source of truth is the numbered migrations in
-- supabase/migrations/.  Run migrations with:
--   supabase db push
-- or apply this file directly against a clean database:
--   psql $DATABASE_URL -f schema.sql
--
-- Dependency order:
--   1. Extensions
--   2. Enums
--   3. Tables (FK-safe ordering)
--   4. Indexes
--   5. Functions & Triggers
-- ================================================================

-- ================================================================
-- 1. EXTENSIONS
-- ================================================================

create extension if not exists vector with schema extensions;    -- pgvector


-- ================================================================
-- 2. ENUMS
-- ================================================================

create type severity_level as enum ('critical', 'high', 'medium', 'low');
create type item_status     as enum ('open', 'in_progress', 'resolved', 'closed');
create type user_role       as enum ('owner', 'admin', 'analyst', 'viewer');
create type evidence_type   as enum (
  'ticket_pattern',
  'deploy_correlation',
  'customer_impact',
  'similar_ticket'
);
create type report_type     as enum ('executive_summary', 'cluster_detail', 'financial_impact', 'custom');
create type deploy_risk     as enum ('critical', 'high', 'medium', 'low');


-- ================================================================
-- 3. TABLES
-- ================================================================

-- ----------------------------------------------------------------
-- 3.1  users
-- ----------------------------------------------------------------
create table public.users (
  id              uuid          primary key references auth.users (id) on delete cascade,
  name            text          not null,
  email           text          not null unique,
  initials        text          not null default '',
  role            user_role     not null default 'viewer',
  company         text,
  plan            text          not null default 'free',
  timezone        text          not null default 'UTC',
  status          text          not null default 'active'
                    check (status in ('active', 'invited', 'suspended')),
  avatar_url      text,
  joined_at       timestamptz   not null default now(),
  last_active_at  timestamptz,
  created_at      timestamptz   not null default now(),
  updated_at      timestamptz   not null default now()
);

comment on table  public.users              is 'Extended user profiles linked to Supabase auth identities.';
comment on column public.users.role         is 'Platform role: owner > admin > analyst > viewer.';
comment on column public.users.plan         is 'Billing plan: free | starter | pro | enterprise.';


-- ----------------------------------------------------------------
-- 3.2  deployments
-- ----------------------------------------------------------------
create table public.deployments (
  id            text          primary key,
  version       text          not null,
  title         text          not null,
  notes         text,
  risk          deploy_risk   not null default 'low',
  deployed_at   date          not null,
  deployed_by   uuid          references public.users (id) on delete set null,
  repository    text,
  commit_sha    text,
  rollback_of   text          references public.deployments (id) on delete set null,
  created_at    timestamptz   not null default now(),
  updated_at    timestamptz   not null default now()
);

comment on table  public.deployments             is 'Software release events correlated with ticket spikes.';
comment on column public.deployments.risk        is 'Pre-deploy risk assessment used in timeline view.';
comment on column public.deployments.rollback_of is 'Self-referential FK when this deploy is a hotfix/rollback.';


-- ----------------------------------------------------------------
-- 3.3  tickets
-- ----------------------------------------------------------------
create table public.tickets (
  id                 bigserial     primary key,
  external_id        text          unique,
  source             text          not null default 'csv'
                       check (source in ('csv', 'zendesk', 'intercom', 'logs', 'manual')),
  title              text          not null,
  body               text,
  customer_id        text,
  customer_email     text,
  severity           severity_level,
  status             item_status   not null default 'open',
  sentiment_score    numeric(4,3)  check (sentiment_score between -1 and 1),
  channel            text,
  tags               text[],
  related_deploy_id  text          references public.deployments (id) on delete set null,
  embedding          extensions.vector(1536),
  ingested_at        timestamptz   not null default now(),
  ticket_created_at  timestamptz,
  resolved_at        timestamptz,
  created_at         timestamptz   not null default now(),
  updated_at         timestamptz   not null default now()
);

comment on table  public.tickets           is 'Raw ingested support tickets from all connected data sources.';
comment on column public.tickets.embedding is '1536-dim OpenAI embedding used for semantic clustering.';


-- ----------------------------------------------------------------
-- 3.4  ticket_clusters
-- ----------------------------------------------------------------
create table public.ticket_clusters (
  id                  text          primary key,
  title               text          not null,
  summary             text,
  severity            severity_level not null default 'medium',
  status              item_status    not null default 'open',
  ticket_count        integer        not null default 0,
  affected_customers  integer        not null default 0,
  monthly_cost_usd    numeric(12,2)  not null default 0,
  confidence          numeric(5,2)   check (confidence between 0 and 100),
  root_cause          text,
  product_area        text,
  ticket_trend        numeric[]      not null default '{}',
  example_titles      text[]         not null default '{}',
  related_deploy_id   text           references public.deployments (id) on delete set null,
  centroid_embedding  extensions.vector(1536),
  first_seen_at       date,
  last_seen_at        date,
  created_by          uuid           references public.users (id) on delete set null,
  created_at          timestamptz    not null default now(),
  updated_at          timestamptz    not null default now()
);

comment on table  public.ticket_clusters                  is 'AI-generated semantic clusters of related support tickets.';
comment on column public.ticket_clusters.ticket_trend     is 'Rolling daily ticket volume (JSON array, newest last).';
comment on column public.ticket_clusters.centroid_embedding is 'Mean embedding of member tickets for ANN search.';


-- ----------------------------------------------------------------
-- 3.5  cluster_tickets  (junction)
-- ----------------------------------------------------------------
create table public.cluster_tickets (
  cluster_id  text    not null references public.ticket_clusters (id) on delete cascade,
  ticket_id   bigint  not null references public.tickets (id) on delete cascade,
  similarity  numeric(5,4),
  primary key (cluster_id, ticket_id)
);

comment on table public.cluster_tickets is 'Many-to-many mapping between clusters and their constituent tickets.';


-- ----------------------------------------------------------------
-- 3.6  investigations
-- ----------------------------------------------------------------
create table public.investigations (
  id                        text           primary key,
  cluster_id                text           not null references public.ticket_clusters (id) on delete cascade,
  root_cause                text           not null,
  confidence                numeric(5,2)   check (confidence between 0 and 100),
  impact_level              severity_level not null,
  affected_customers        integer        not null default 0,
  revenue_impact_usd        numeric(12,2)  not null default 0,
  deploy_correlation_id     text           references public.deployments (id) on delete set null,
  deploy_correlation_score  numeric(5,4),
  reasoning_steps           text[]         not null default '{}',
  sim_before_ticket_count   integer,
  sim_after_ticket_count    integer,
  sim_deflection_pct        numeric(5,2),
  sim_recovered_usd         numeric(12,2),
  model_version             text           not null default 'fixloop-reasoner-v3',
  created_by                uuid           references public.users (id) on delete set null,
  approved_by               uuid           references public.users (id) on delete set null,
  approved_at               timestamptz,
  created_at                timestamptz    not null default now(),
  updated_at                timestamptz    not null default now()
);

comment on table public.investigations is 'AI root-cause investigation reports linked to clusters.';


-- ----------------------------------------------------------------
-- 3.7  investigation_evidence
-- ----------------------------------------------------------------
create table public.investigation_evidence (
  id               text          primary key,
  investigation_id text          not null references public.investigations (id) on delete cascade,
  evidence_type    evidence_type not null,
  title            text          not null,
  detail           text,
  weight           numeric(5,4)  not null default 0 check (weight between 0 and 1),
  sort_order       smallint      not null default 0,
  created_at       timestamptz   not null default now()
);

comment on table  public.investigation_evidence        is 'Weighted evidence items that support an AI investigation.';
comment on column public.investigation_evidence.weight is '0.0–1.0 signal weight used to render evidence bars.';


-- ----------------------------------------------------------------
-- 3.8  fix_recommendations
-- ----------------------------------------------------------------
create table public.fix_recommendations (
  id                      text          primary key,
  cluster_id              text          not null references public.ticket_clusters (id) on delete cascade,
  investigation_id        text          references public.investigations (id) on delete set null,
  title                   text          not null,
  description             text          not null,
  owner_name              text,
  owner_user_id           uuid          references public.users (id) on delete set null,
  status                  item_status   not null default 'open',
  expected_reduction_pct  numeric(5,2),
  expected_recovery_usd   numeric(12,2),
  actual_reduction_pct    numeric(5,2),
  actual_recovery_usd     numeric(12,2),
  before_ticket_count     integer,
  after_ticket_count      integer,
  estimated_eta           text,
  external_ticket_url     text,
  created_by              uuid          references public.users (id) on delete set null,
  resolved_by             uuid          references public.users (id) on delete set null,
  resolved_at             timestamptz,
  created_at              timestamptz   not null default now(),
  updated_at              timestamptz   not null default now()
);

comment on table public.fix_recommendations is 'Actionable fix plans produced by AI investigations.';


-- ----------------------------------------------------------------
-- 3.9  validation_results
-- ----------------------------------------------------------------
create table public.validation_results (
  id                     bigserial     primary key,
  fix_recommendation_id  text          not null references public.fix_recommendations (id) on delete cascade,
  measurement_date       date          not null default current_date,
  period_label           text,
  ticket_count           integer       not null,
  deflection_pct         numeric(5,2),
  revenue_recovered_usd  numeric(12,2),
  notes                  text,
  measured_by            uuid          references public.users (id) on delete set null,
  created_at             timestamptz   not null default now()
);

comment on table public.validation_results is 'Measured before/after metrics that validate a shipped fix.';


-- ----------------------------------------------------------------
-- 3.10  reports
-- ----------------------------------------------------------------
create table public.reports (
  id                     bigserial     primary key,
  report_type            report_type   not null default 'executive_summary',
  title                  text          not null,
  quarter                text,
  date_from              date,
  date_to                date,
  cluster_ids            text[],
  total_tickets          integer,
  active_clusters        integer,
  revenue_at_risk_usd    numeric(14,2),
  revenue_recovered_usd  numeric(14,2),
  deflection_rate        numeric(5,4),
  summary_html           text,
  storage_path           text,
  created_by             uuid          references public.users (id) on delete set null,
  created_at             timestamptz   not null default now()
);

comment on table public.reports is 'Exported intelligence reports (executive, cluster, financial).';


-- ================================================================
-- 4. INDEXES
-- ================================================================

-- users
create index idx_users_email        on public.users (email);
create index idx_users_role         on public.users (role);
create index idx_users_status       on public.users (status);

-- deployments
create index idx_deployments_deployed_at on public.deployments (deployed_at desc);
create index idx_deployments_version     on public.deployments (version);
create index idx_deployments_risk        on public.deployments (risk);

-- tickets
create index idx_tickets_status          on public.tickets (status);
create index idx_tickets_severity        on public.tickets (severity);
create index idx_tickets_source          on public.tickets (source);
create index idx_tickets_customer_id     on public.tickets (customer_id);
create index idx_tickets_related_deploy  on public.tickets (related_deploy_id);
create index idx_tickets_ingested_at     on public.tickets (ingested_at desc);
create index idx_tickets_tags            on public.tickets using gin (tags);
create index idx_tickets_embedding       on public.tickets
  using ivfflat (embedding extensions.vector_cosine_ops)
  with (lists = 100);

-- ticket_clusters
create index idx_clusters_severity       on public.ticket_clusters (severity);
create index idx_clusters_status         on public.ticket_clusters (status);
create index idx_clusters_monthly_cost   on public.ticket_clusters (monthly_cost_usd desc);
create index idx_clusters_product_area   on public.ticket_clusters (product_area);
create index idx_clusters_first_seen     on public.ticket_clusters (first_seen_at desc);
create index idx_clusters_related_deploy on public.ticket_clusters (related_deploy_id);
create index idx_clusters_centroid       on public.ticket_clusters
  using ivfflat (centroid_embedding extensions.vector_cosine_ops)
  with (lists = 50);

-- cluster_tickets
create index idx_cluster_tickets_ticket  on public.cluster_tickets (ticket_id);

-- investigations
create index idx_investigations_cluster    on public.investigations (cluster_id);
create index idx_investigations_impact     on public.investigations (impact_level);
create index idx_investigations_confidence on public.investigations (confidence desc);
create index idx_investigations_deploy     on public.investigations (deploy_correlation_id);

-- investigation_evidence
create index idx_evidence_investigation  on public.investigation_evidence (investigation_id, sort_order);

-- fix_recommendations
create index idx_fix_rec_cluster        on public.fix_recommendations (cluster_id);
create index idx_fix_rec_investigation  on public.fix_recommendations (investigation_id);
create index idx_fix_rec_status         on public.fix_recommendations (status);
create index idx_fix_rec_owner          on public.fix_recommendations (owner_user_id);

-- validation_results
create index idx_validation_fix         on public.validation_results (fix_recommendation_id);
create index idx_validation_date        on public.validation_results (measurement_date desc);

-- reports
create index idx_reports_type           on public.reports (report_type);
create index idx_reports_created_at     on public.reports (created_at desc);
create index idx_reports_created_by     on public.reports (created_by);


-- ================================================================
-- 5. FUNCTIONS & TRIGGERS
-- ================================================================

-- updated_at auto-stamp
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_users_updated_at          before update on public.users           for each row execute function public.set_updated_at();
create trigger trg_deployments_updated_at    before update on public.deployments     for each row execute function public.set_updated_at();
create trigger trg_tickets_updated_at        before update on public.tickets         for each row execute function public.set_updated_at();
create trigger trg_clusters_updated_at       before update on public.ticket_clusters for each row execute function public.set_updated_at();
create trigger trg_investigations_updated_at before update on public.investigations  for each row execute function public.set_updated_at();
create trigger trg_fix_rec_updated_at        before update on public.fix_recommendations for each row execute function public.set_updated_at();

-- Cluster ticket-count sync
create or replace function public.sync_cluster_ticket_count()
returns trigger language plpgsql as $$
begin
  if (tg_op = 'INSERT') then
    update public.ticket_clusters set ticket_count = ticket_count + 1, updated_at = now() where id = new.cluster_id;
  elsif (tg_op = 'DELETE') then
    update public.ticket_clusters set ticket_count = greatest(ticket_count - 1, 0), updated_at = now() where id = old.cluster_id;
  end if;
  return null;
end;
$$;

create trigger trg_cluster_tickets_count
  after insert or delete on public.cluster_tickets
  for each row execute function public.sync_cluster_ticket_count();

-- Semantic search: tickets
create or replace function public.match_tickets(
  query_embedding  extensions.vector(1536),
  match_threshold  float  default 0.75,
  match_count      int    default 20
)
returns table (id bigint, title text, body text, severity severity_level, status item_status, similarity float)
language sql stable as $$
  select t.id, t.title, t.body, t.severity, t.status,
         1 - (t.embedding <=> query_embedding) as similarity
  from public.tickets t
  where t.embedding is not null
    and 1 - (t.embedding <=> query_embedding) > match_threshold
  order by t.embedding <=> query_embedding
  limit match_count;
$$;

-- Semantic search: clusters
create or replace function public.match_clusters(
  query_embedding  extensions.vector(1536),
  match_threshold  float  default 0.70,
  match_count      int    default 10
)
returns table (id text, title text, severity severity_level, monthly_cost_usd numeric, similarity float)
language sql stable as $$
  select c.id, c.title, c.severity, c.monthly_cost_usd,
         1 - (c.centroid_embedding <=> query_embedding) as similarity
  from public.ticket_clusters c
  where c.centroid_embedding is not null
    and 1 - (c.centroid_embedding <=> query_embedding) > match_threshold
  order by c.centroid_embedding <=> query_embedding
  limit match_count;
$$;

-- Dashboard KPI aggregate
create or replace function public.get_dashboard_kpis()
returns json language sql stable as $$
  select json_build_object(
    'total_tickets',          (select count(*)                      from public.tickets),
    'open_clusters',          (select count(*)                      from public.ticket_clusters where status = 'open'),
    'affected_customers',     (select coalesce(sum(affected_customers),0) from public.ticket_clusters where status = 'open'),
    'revenue_at_risk_usd',    (select coalesce(sum(monthly_cost_usd),0)   from public.ticket_clusters where status = 'open'),
    'revenue_recovered_usd',  (select coalesce(sum(actual_recovery_usd),0) from public.fix_recommendations where status = 'resolved'),
    'resolved_pct',           (
      select round(count(*) filter (where status='resolved')::numeric / nullif(count(*),0) * 100, 1)
      from public.fix_recommendations
    )
  );
$$;

-- New-user profile auto-creation
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.users (id, email, name, initials, role)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    upper(left(coalesce(new.raw_user_meta_data->>'full_name', new.email), 2)),
    'viewer'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger trg_on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();


-- ================================================================
-- 6. ROW LEVEL SECURITY
-- ================================================================

alter table public.users                  enable row level security;
alter table public.deployments            enable row level security;
alter table public.tickets                enable row level security;
alter table public.ticket_clusters        enable row level security;
alter table public.cluster_tickets        enable row level security;
alter table public.investigations         enable row level security;
alter table public.investigation_evidence enable row level security;
alter table public.fix_recommendations    enable row level security;
alter table public.validation_results     enable row level security;
alter table public.reports                enable row level security;

-- All authenticated users can read platform data
create policy "rls_read_users"               on public.users                  for select using (auth.uid() = id or exists(select 1 from public.users u where u.id=auth.uid() and u.role in ('owner','admin')));
create policy "rls_read_deployments"         on public.deployments            for select using (auth.role() = 'authenticated');
create policy "rls_read_tickets"             on public.tickets                for select using (auth.role() = 'authenticated');
create policy "rls_read_clusters"            on public.ticket_clusters        for select using (auth.role() = 'authenticated');
create policy "rls_read_cluster_tickets"     on public.cluster_tickets        for select using (auth.role() = 'authenticated');
create policy "rls_read_investigations"      on public.investigations         for select using (auth.role() = 'authenticated');
create policy "rls_read_evidence"            on public.investigation_evidence for select using (auth.role() = 'authenticated');
create policy "rls_read_fix_recommendations" on public.fix_recommendations    for select using (auth.role() = 'authenticated');
create policy "rls_read_validation_results"  on public.validation_results     for select using (auth.role() = 'authenticated');
create policy "rls_read_reports"             on public.reports                for select using (auth.role() = 'authenticated');

-- Analysts can write tickets, clusters, investigations, fix recommendations
create policy "rls_insert_tickets"        on public.tickets             for insert with check (auth.role() = 'authenticated');
create policy "rls_update_tickets"        on public.tickets             for update using  (auth.role() = 'authenticated');
create policy "rls_insert_clusters"       on public.ticket_clusters     for insert with check (auth.role() = 'authenticated');
create policy "rls_update_clusters"       on public.ticket_clusters     for update using  (auth.role() = 'authenticated');
create policy "rls_insert_investigations" on public.investigations       for insert with check (auth.role() = 'authenticated');
create policy "rls_update_investigations" on public.investigations       for update using  (auth.role() = 'authenticated');
create policy "rls_insert_fix_rec"        on public.fix_recommendations  for insert with check (auth.role() = 'authenticated');
create policy "rls_update_fix_rec"        on public.fix_recommendations  for update using  (auth.role() = 'authenticated');
create policy "rls_insert_validation"     on public.validation_results   for insert with check (auth.role() = 'authenticated');
create policy "rls_insert_reports"        on public.reports              for insert with check (auth.role() = 'authenticated');

-- Admins only: deployments write
create policy "rls_insert_deployments" on public.deployments for insert with check (exists(select 1 from public.users u where u.id=auth.uid() and u.role in ('owner','admin')));
create policy "rls_update_deployments" on public.deployments for update using        (exists(select 1 from public.users u where u.id=auth.uid() and u.role in ('owner','admin')));
