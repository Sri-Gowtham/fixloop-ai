# FixLoop AI — Supabase Database Setup

## File Structure

```
supabase/
├── config.toml               Supabase CLI local dev configuration
├── schema.sql                Consolidated reference schema (all-in-one)
├── seed.sql                  Seed data derived from mock-data.ts
└── migrations/
    ├── 00001_enable_pgvector.sql    Enable pgvector extension
    ├── 00002_create_enums.sql       Domain enumerations
    ├── 00003_create_tables.sql      All 8 tables with FK + indexes
    ├── 00004_rls_policies.sql       Row Level Security policies
    └── 00005_functions_triggers.sql Triggers, ANN search functions, KPI aggregate
```

---

## Tables

| Table | Purpose |
|---|---|
| `users` | User profiles extended from `auth.users` |
| `deployments` | Release events correlated with ticket spikes |
| `tickets` | Raw ingested support tickets (with pgvector embedding) |
| `ticket_clusters` | AI semantic clusters with centroid embedding |
| `cluster_tickets` | Many-to-many junction between clusters and tickets |
| `investigations` | AI root-cause investigation reports |
| `investigation_evidence` | Weighted evidence items per investigation |
| `fix_recommendations` | Actionable fix plans linked to clusters |
| `validation_results` | Before/after measurements validating shipped fixes |
| `reports` | Exported executive / cluster reports |

---

## Key Design Decisions

- **pgvector (IVFFlat)** — `tickets.embedding` (1536-dim) and `ticket_clusters.centroid_embedding` use `ivfflat` ANN indexes with cosine distance for semantic search and clustering.
- **`match_tickets()` / `match_clusters()`** — PostgreSQL functions expose vector similarity search directly to the API layer.
- **`get_dashboard_kpis()`** — Single-row JSON aggregate used by the dashboard endpoint.
- **Auto-updated `updated_at`** — A shared trigger function stamps every mutated row.
- **`sync_cluster_ticket_count()`** — Trigger keeps `ticket_clusters.ticket_count` in sync without application-level bookkeeping.
- **RLS** — All tables have Row Level Security enabled. Reads are open to any authenticated user; writes are role-scoped; the service role key bypasses all policies for the AI pipeline.

---

## Getting Started

### Local Development (Supabase CLI)

```bash
# Install Supabase CLI
npm install -g supabase

# Start local Supabase stack
supabase start

# Apply migrations
supabase db push

# Seed development data
psql $(supabase db url) -f supabase/seed.sql

# Open Studio
supabase studio
```

### Remote / Production

```bash
# Link to your Supabase project
supabase link --project-ref <your-project-ref>

# Push migrations to remote
supabase db push

# Seed (run once against staging)
psql $DATABASE_URL -f supabase/seed.sql
```

---

## pgvector Notes

The embedding column uses **1536 dimensions** matching OpenAI `text-embedding-3-small` / `ada-002`.

- IVFFlat `lists = 100` for tickets (~12k rows seed, scales to ~1M).
- IVFFlat `lists = 50` for clusters (~10–1000 clusters expected).
- Adjust `lists` as data grows: a good rule of thumb is `sqrt(row_count)`.
- Run `ANALYZE` after bulk inserts to keep the planner statistics fresh.

---

## Environment Variables

```env
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
```
