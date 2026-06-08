-- ============================================================
-- Migration: 00005_functions_triggers
-- Purpose  : Helper functions, update triggers, and
--            aggregate utility functions for the API layer.
-- ============================================================

-- ------------------------------------------------------------
-- A. updated_at auto-stamp trigger function
-- ------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Attach to every table that has an updated_at column
create trigger trg_users_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();

create trigger trg_deployments_updated_at
  before update on public.deployments
  for each row execute function public.set_updated_at();

create trigger trg_tickets_updated_at
  before update on public.tickets
  for each row execute function public.set_updated_at();

create trigger trg_clusters_updated_at
  before update on public.ticket_clusters
  for each row execute function public.set_updated_at();

create trigger trg_investigations_updated_at
  before update on public.investigations
  for each row execute function public.set_updated_at();

create trigger trg_fix_rec_updated_at
  before update on public.fix_recommendations
  for each row execute function public.set_updated_at();


-- ------------------------------------------------------------
-- B. Keep ticket_clusters.ticket_count in sync
-- ------------------------------------------------------------
create or replace function public.sync_cluster_ticket_count()
returns trigger
language plpgsql
as $$
begin
  if (tg_op = 'INSERT') then
    update public.ticket_clusters
    set ticket_count = ticket_count + 1,
        updated_at   = now()
    where id = new.cluster_id;
  elsif (tg_op = 'DELETE') then
    update public.ticket_clusters
    set ticket_count = greatest(ticket_count - 1, 0),
        updated_at   = now()
    where id = old.cluster_id;
  end if;
  return null;
end;
$$;

create trigger trg_cluster_tickets_count
  after insert or delete on public.cluster_tickets
  for each row execute function public.sync_cluster_ticket_count();


-- ------------------------------------------------------------
-- C. Semantic nearest-neighbour search on tickets
--    Returns the k most similar tickets to a query vector.
-- ------------------------------------------------------------
create or replace function public.match_tickets(
  query_embedding  extensions.vector(1536),
  match_threshold  float   default 0.75,
  match_count      int     default 20
)
returns table (
  id               bigint,
  title            text,
  body             text,
  severity         severity_level,
  status           item_status,
  similarity       float
)
language sql stable
as $$
  select
    t.id,
    t.title,
    t.body,
    t.severity,
    t.status,
    1 - (t.embedding <=> query_embedding) as similarity
  from public.tickets t
  where t.embedding is not null
    and 1 - (t.embedding <=> query_embedding) > match_threshold
  order by t.embedding <=> query_embedding
  limit match_count;
$$;

comment on function public.match_tickets is
  'Returns up to match_count tickets whose embedding is within match_threshold cosine similarity.';


-- ------------------------------------------------------------
-- D. Find clusters near a query embedding (copilot / search)
-- ------------------------------------------------------------
create or replace function public.match_clusters(
  query_embedding  extensions.vector(1536),
  match_threshold  float  default 0.70,
  match_count      int    default 10
)
returns table (
  id                text,
  title             text,
  severity          severity_level,
  monthly_cost_usd  numeric,
  similarity        float
)
language sql stable
as $$
  select
    c.id,
    c.title,
    c.severity,
    c.monthly_cost_usd,
    1 - (c.centroid_embedding <=> query_embedding) as similarity
  from public.ticket_clusters c
  where c.centroid_embedding is not null
    and 1 - (c.centroid_embedding <=> query_embedding) > match_threshold
  order by c.centroid_embedding <=> query_embedding
  limit match_count;
$$;

comment on function public.match_clusters is
  'Returns clusters most semantically similar to a query embedding — used by the Copilot.';


-- ------------------------------------------------------------
-- E. Dashboard KPIs — single-row aggregate for the API
-- ------------------------------------------------------------
create or replace function public.get_dashboard_kpis()
returns json
language sql stable
as $$
  select json_build_object(
    'total_tickets',           (select count(*) from public.tickets),
    'open_clusters',           (select count(*) from public.ticket_clusters where status = 'open'),
    'affected_customers',      (select coalesce(sum(affected_customers), 0) from public.ticket_clusters where status = 'open'),
    'revenue_at_risk_usd',     (select coalesce(sum(monthly_cost_usd), 0) from public.ticket_clusters where status = 'open'),
    'revenue_recovered_usd',   (select coalesce(sum(actual_recovery_usd), 0) from public.fix_recommendations where status = 'resolved'),
    'resolved_pct',            (
      select round(
        count(*) filter (where status = 'resolved')::numeric
        / nullif(count(*), 0) * 100, 1
      )
      from public.fix_recommendations
    )
  );
$$;

comment on function public.get_dashboard_kpis is
  'Returns a single JSON object with all dashboard KPI aggregates.';


-- ------------------------------------------------------------
-- F. New-user handler — auto-insert profile row from auth.users
-- ------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
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
