-- ============================================================
-- Migration: 00003_create_tables
-- Purpose  : Core FixLoop AI relational schema
--            Tables created in dependency order so FK
--            references are always satisfied.
-- ============================================================

-- ------------------------------------------------------------
-- 1. USERS
--    Supabase auth.users is extended with a profile row here.
-- ------------------------------------------------------------
create table public.users (
  id            uuid        primary key references auth.users (id) on delete cascade,
  name          text        not null,
  email         text        not null unique,
  initials      text        not null default '',
  role          user_role   not null default 'viewer',
  company       text,
  plan          text        not null default 'free',
  timezone      text        not null default 'UTC',
  status        text        not null default 'active'  check (status in ('active', 'invited', 'suspended')),
  avatar_url    text,
  joined_at     timestamptz not null default now(),
  last_active_at timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

comment on table public.users is 'Extended user profiles linked to Supabase auth identities.';


-- ------------------------------------------------------------
-- 2. DEPLOYMENTS
--    Release events used for deploy-correlation analysis.
--    Created before tickets so tickets can FK to deploys.
-- ------------------------------------------------------------
create table public.deployments (
  id            text        primary key,                        -- e.g. "D-006"
  version       text        not null,                          -- e.g. "v2.4.3"
  title         text        not null,
  notes         text,
  risk          deploy_risk not null default 'low',
  deployed_at   date        not null,
  deployed_by   uuid        references public.users (id) on delete set null,
  repository    text,                                           -- GitHub repo slug
  commit_sha    text,
  rollback_of   text        references public.deployments (id) on delete set null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

comment on table public.deployments is 'Software release events correlated with ticket spikes.';

create index idx_deployments_deployed_at on public.deployments (deployed_at desc);
create index idx_deployments_version     on public.deployments (version);


-- ------------------------------------------------------------
-- 3. TICKETS
--    Raw ingested support tickets from Zendesk / CSV / logs.
--    embedding column stores pgvector representation for
--    semantic clustering.
-- ------------------------------------------------------------
create table public.tickets (
  id                 bigserial   primary key,
  external_id        text        unique,                        -- Zendesk / source system ID
  source             text        not null default 'csv'         -- 'csv', 'zendesk', 'intercom', 'logs'
                       check (source in ('csv', 'zendesk', 'intercom', 'logs', 'manual')),
  title              text        not null,
  body               text,
  customer_id        text,                                      -- opaque external customer identifier
  customer_email     text,
  severity           severity_level,
  status             item_status not null default 'open',
  sentiment_score    numeric(4,3)                               -- -1.0 to 1.0
                       check (sentiment_score between -1 and 1),
  channel            text,                                      -- 'email', 'chat', 'phone'
  tags               text[],
  related_deploy_id  text        references public.deployments (id) on delete set null,
  embedding          extensions.vector(1536),                   -- OpenAI ada-002 / text-embedding-3-small
  ingested_at        timestamptz not null default now(),
  ticket_created_at  timestamptz,
  resolved_at        timestamptz,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

comment on table public.tickets is 'Raw ingested support tickets from all connected sources.';
comment on column public.tickets.embedding is 'pgvector embedding (1536-dim) for semantic clustering.';

create index idx_tickets_status           on public.tickets (status);
create index idx_tickets_severity         on public.tickets (severity);
create index idx_tickets_source           on public.tickets (source);
create index idx_tickets_customer_id      on public.tickets (customer_id);
create index idx_tickets_related_deploy   on public.tickets (related_deploy_id);
create index idx_tickets_ingested_at      on public.tickets (ingested_at desc);
create index idx_tickets_embedding        on public.tickets using ivfflat (embedding extensions.vector_cosine_ops)
  with (lists = 100);


-- ------------------------------------------------------------
-- 4. TICKET_CLUSTERS
--    Semantic clusters produced by the AI clustering pipeline.
-- ------------------------------------------------------------
create table public.ticket_clusters (
  id                 text        primary key,                   -- e.g. "CL-1042"
  title              text        not null,
  summary            text,
  severity           severity_level not null default 'medium',
  status             item_status not null default 'open',
  ticket_count       integer     not null default 0,
  affected_customers integer     not null default 0,
  monthly_cost_usd   numeric(12,2) not null default 0,          -- revenue at risk / month
  confidence         numeric(5,2)                               -- 0-100 %
                       check (confidence between 0 and 100),
  root_cause         text,
  product_area       text,
  ticket_trend       numeric[]   not null default '{}',         -- rolling daily counts (sparkline data)
  example_titles     text[]      not null default '{}',         -- representative ticket titles
  related_deploy_id  text        references public.deployments (id) on delete set null,
  centroid_embedding extensions.vector(1536),                   -- cluster centroid for nearest-neighbour
  first_seen_at      date,
  last_seen_at       date,
  created_by         uuid        references public.users (id) on delete set null,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

comment on table public.ticket_clusters is 'AI-generated semantic clusters of related support tickets.';
comment on column public.ticket_clusters.centroid_embedding is 'Mean embedding vector of all tickets in the cluster.';

create index idx_clusters_severity       on public.ticket_clusters (severity);
create index idx_clusters_status         on public.ticket_clusters (status);
create index idx_clusters_monthly_cost   on public.ticket_clusters (monthly_cost_usd desc);
create index idx_clusters_product_area   on public.ticket_clusters (product_area);
create index idx_clusters_first_seen     on public.ticket_clusters (first_seen_at desc);
create index idx_clusters_related_deploy on public.ticket_clusters (related_deploy_id);
create index idx_clusters_centroid       on public.ticket_clusters using ivfflat (centroid_embedding extensions.vector_cosine_ops)
  with (lists = 50);


-- Junction table: cluster ↔ ticket (many-to-many)
create table public.cluster_tickets (
  cluster_id  text    not null references public.ticket_clusters (id) on delete cascade,
  ticket_id   bigint  not null references public.tickets (id) on delete cascade,
  similarity  numeric(5,4),                                     -- cosine similarity to centroid
  primary key (cluster_id, ticket_id)
);

create index idx_cluster_tickets_ticket on public.cluster_tickets (ticket_id);


-- ------------------------------------------------------------
-- 5. INVESTIGATIONS
--    AI-generated root-cause investigation reports.
-- ------------------------------------------------------------
create table public.investigations (
  id                        text        primary key,            -- e.g. "AI-7741"
  cluster_id                text        not null references public.ticket_clusters (id) on delete cascade,
  root_cause                text        not null,
  confidence                numeric(5,2)
                              check (confidence between 0 and 100),
  impact_level              severity_level not null,
  affected_customers        integer     not null default 0,
  revenue_impact_usd        numeric(12,2) not null default 0,
  deploy_correlation_id     text        references public.deployments (id) on delete set null,
  deploy_correlation_score  numeric(5,4),                       -- 0.0 – 1.0 Pearson-like score
  reasoning_steps           text[]      not null default '{}',  -- ordered explainability chain
  sim_before_ticket_count   integer,                            -- Fix Validation Simulator: before
  sim_after_ticket_count    integer,                            -- Fix Validation Simulator: after
  sim_deflection_pct        numeric(5,2),
  sim_recovered_usd         numeric(12,2),
  model_version             text        not null default 'fixloop-reasoner-v3',
  created_by                uuid        references public.users (id) on delete set null,
  approved_by               uuid        references public.users (id) on delete set null,
  approved_at               timestamptz,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

comment on table public.investigations is 'AI root-cause investigation reports linked to clusters.';

create index idx_investigations_cluster    on public.investigations (cluster_id);
create index idx_investigations_impact     on public.investigations (impact_level);
create index idx_investigations_confidence on public.investigations (confidence desc);
create index idx_investigations_deploy     on public.investigations (deploy_correlation_id);


-- Evidence items for each investigation (accordion rows in AI Command Center)
create table public.investigation_evidence (
  id               text        primary key,                     -- e.g. "E-1"
  investigation_id text        not null references public.investigations (id) on delete cascade,
  evidence_type    evidence_type not null,
  title            text        not null,
  detail           text,
  weight           numeric(5,4) not null default 0
                     check (weight between 0 and 1),
  sort_order       smallint    not null default 0,
  created_at       timestamptz not null default now()
);

comment on table public.investigation_evidence is 'Weighted evidence items that support an AI investigation conclusion.';

create index idx_evidence_investigation on public.investigation_evidence (investigation_id, sort_order);


-- ------------------------------------------------------------
-- 6. FIX_RECOMMENDATIONS
--    Actionable fix plans linked to investigations / clusters.
-- ------------------------------------------------------------
create table public.fix_recommendations (
  id                   text        primary key,                 -- e.g. "R-1"
  cluster_id           text        not null references public.ticket_clusters (id) on delete cascade,
  investigation_id     text        references public.investigations (id) on delete set null,
  title                text        not null,
  description          text        not null,
  owner_name           text,
  owner_user_id        uuid        references public.users (id) on delete set null,
  status               item_status not null default 'open',
  expected_reduction_pct numeric(5,2),                          -- expected ticket deflection %
  expected_recovery_usd  numeric(12,2),                         -- expected monthly revenue recovery
  actual_reduction_pct   numeric(5,2),                          -- measured after shipping
  actual_recovery_usd    numeric(12,2),
  before_ticket_count    integer,
  after_ticket_count     integer,
  estimated_eta          text,                                  -- human-readable: "2 days"
  external_ticket_url    text,                                  -- e.g. Jira ticket URL
  created_by           uuid        references public.users (id) on delete set null,
  resolved_by          uuid        references public.users (id) on delete set null,
  resolved_at          timestamptz,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

comment on table public.fix_recommendations is 'Actionable fix plans produced by AI investigations.';

create index idx_fix_rec_cluster        on public.fix_recommendations (cluster_id);
create index idx_fix_rec_investigation  on public.fix_recommendations (investigation_id);
create index idx_fix_rec_status         on public.fix_recommendations (status);
create index idx_fix_rec_owner          on public.fix_recommendations (owner_user_id);


-- ------------------------------------------------------------
-- 7. VALIDATION_RESULTS
--    Before/after measurements that prove a fix worked.
--    Drives the "Resolution Center" loop-closure metrics.
-- ------------------------------------------------------------
create table public.validation_results (
  id                   bigserial   primary key,
  fix_recommendation_id text       not null references public.fix_recommendations (id) on delete cascade,
  measurement_date     date        not null default current_date,
  period_label         text,                                    -- e.g. "Week 1 post-ship"
  ticket_count         integer     not null,
  deflection_pct       numeric(5,2),
  revenue_recovered_usd numeric(12,2),
  notes                text,
  measured_by          uuid        references public.users (id) on delete set null,
  created_at           timestamptz not null default now()
);

comment on table public.validation_results is 'Measured before/after metrics that validate a shipped fix.';

create index idx_validation_fix  on public.validation_results (fix_recommendation_id);
create index idx_validation_date on public.validation_results (measurement_date desc);


-- ------------------------------------------------------------
-- 8. REPORTS
--    Exported executive / cluster reports (PDF / JSON blobs).
-- ------------------------------------------------------------
create table public.reports (
  id            bigserial    primary key,
  report_type   report_type  not null default 'executive_summary',
  title         text         not null,
  quarter       text,                                           -- e.g. "Q2 2026"
  date_from     date,
  date_to       date,
  cluster_ids   text[],                                        -- scoped clusters (null = all)
  total_tickets integer,
  active_clusters integer,
  revenue_at_risk_usd   numeric(14,2),
  revenue_recovered_usd numeric(14,2),
  deflection_rate       numeric(5,4),
  summary_html  text,                                          -- rendered executive prose
  storage_path  text,                                          -- Supabase Storage bucket path for PDF
  created_by    uuid         references public.users (id) on delete set null,
  created_at    timestamptz  not null default now()
);

comment on table public.reports is 'Exported intelligence reports (executive, cluster, financial).';

create index idx_reports_type       on public.reports (report_type);
create index idx_reports_created_at on public.reports (created_at desc);
create index idx_reports_created_by on public.reports (created_by);
