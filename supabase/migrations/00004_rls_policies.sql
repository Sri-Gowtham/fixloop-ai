-- ============================================================
-- Migration: 00004_rls_policies
-- Purpose  : Row Level Security for multi-tenant data isolation
--            All tables require the requesting user to belong
--            to the same organisation (company) as the data.
--            Adjust org_id strategy when multi-tenancy is added.
-- ============================================================

-- Enable RLS on every table
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

-- -----------------------------------------------
-- Authenticated users can read their own profile
-- -----------------------------------------------
create policy "Users can view own profile"
  on public.users for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.users for update
  using (auth.uid() = id);

-- -----------------------------------------------
-- Owners / Admins can manage team members
-- -----------------------------------------------
create policy "Admins can view all users"
  on public.users for select
  using (
    exists (
      select 1 from public.users u
      where u.id = auth.uid()
        and u.role in ('owner', 'admin')
    )
  );

-- -----------------------------------------------
-- Authenticated users can read platform data
-- -----------------------------------------------
create policy "Authenticated users can read deployments"
  on public.deployments for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read tickets"
  on public.tickets for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read clusters"
  on public.ticket_clusters for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read cluster_tickets"
  on public.cluster_tickets for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read investigations"
  on public.investigations for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read evidence"
  on public.investigation_evidence for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read fix recommendations"
  on public.fix_recommendations for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read validation results"
  on public.validation_results for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read reports"
  on public.reports for select
  using (auth.role() = 'authenticated');

-- -----------------------------------------------
-- Write policies (analysts+)
-- -----------------------------------------------
create policy "Analysts can insert tickets"
  on public.tickets for insert
  with check (auth.role() = 'authenticated');

create policy "Analysts can update tickets"
  on public.tickets for update
  using (auth.role() = 'authenticated');

create policy "Analysts can insert clusters"
  on public.ticket_clusters for insert
  with check (auth.role() = 'authenticated');

create policy "Analysts can update clusters"
  on public.ticket_clusters for update
  using (auth.role() = 'authenticated');

create policy "Analysts can insert investigations"
  on public.investigations for insert
  with check (auth.role() = 'authenticated');

create policy "Analysts can update investigations"
  on public.investigations for update
  using (auth.role() = 'authenticated');

create policy "Analysts can insert fix recommendations"
  on public.fix_recommendations for insert
  with check (auth.role() = 'authenticated');

create policy "Analysts can update fix recommendations"
  on public.fix_recommendations for update
  using (auth.role() = 'authenticated');

create policy "Analysts can insert validation results"
  on public.validation_results for insert
  with check (auth.role() = 'authenticated');

create policy "Analysts can insert reports"
  on public.reports for insert
  with check (auth.role() = 'authenticated');

-- -----------------------------------------------
-- Admin-only: deployments write
-- -----------------------------------------------
create policy "Admins can insert deployments"
  on public.deployments for insert
  with check (
    exists (
      select 1 from public.users u
      where u.id = auth.uid()
        and u.role in ('owner', 'admin')
    )
  );

create policy "Admins can update deployments"
  on public.deployments for update
  using (
    exists (
      select 1 from public.users u
      where u.id = auth.uid()
        and u.role in ('owner', 'admin')
    )
  );

-- -----------------------------------------------
-- Service role bypass (backend / AI pipeline)
-- -----------------------------------------------
-- All policies are bypassed by the service_role key,
-- which is used by the FastAPI backend and AI workers.
