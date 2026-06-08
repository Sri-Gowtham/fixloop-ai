-- ================================================================
-- seed.sql — FixLoop AI
-- ================================================================
-- Representative seed data derived from the mock-data.ts source
-- of truth.  Run after schema.sql / migrations on a development
-- or staging database:
--
--   psql $DATABASE_URL -f supabase/seed.sql
--
-- NOTE: auth.users rows must be created via Supabase Auth before
-- running this file, OR use the placeholder UUIDs below with
-- direct insertion into auth.users for local development.
-- ================================================================

-- ================================================================
-- 0. DEVELOPMENT PLACEHOLDER AUTH USERS
--    Insert only in dev/staging — never in production.
--    These map to the TeamMember records in mock-data.ts.
-- ================================================================

-- In production, remove this block and let Supabase Auth manage
-- auth.users via sign-up/invite flows.
do $$
begin
  -- Only seed auth users when the table is empty (safety guard)
  if not exists (select 1 from auth.users limit 1) then
    insert into auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at, raw_user_meta_data)
    values
      ('00000000-0000-0000-0000-000000000001', 'nadia.khan@acmecorp.com',   '$2a$10$placeholder_hash_nadia',   now(), now(), now(), '{"full_name":"Nadia Khan"}'),
      ('00000000-0000-0000-0000-000000000002', 'marcus.lee@acmecorp.com',   '$2a$10$placeholder_hash_marcus',  now(), now(), now(), '{"full_name":"Marcus Lee"}'),
      ('00000000-0000-0000-0000-000000000003', 'priya.r@acmecorp.com',      '$2a$10$placeholder_hash_priya',   now(), now(), now(), '{"full_name":"Priya Raman"}'),
      ('00000000-0000-0000-0000-000000000004', 'jonas.w@acmecorp.com',      '$2a$10$placeholder_hash_jonas',   now(), now(), now(), '{"full_name":"Jonas Weber"}'),
      ('00000000-0000-0000-0000-000000000005', 'sofia@acmecorp.com',        '$2a$10$placeholder_hash_sofia',   now(), now(), now(), '{"full_name":"Sofia Alvarez"}'),
      ('00000000-0000-0000-0000-000000000006', 'devon.park@acmecorp.com',   '$2a$10$placeholder_hash_devon',   now(), now(), now(), '{"full_name":"Devon Park"}');
  end if;
end
$$;


-- ================================================================
-- 1. USERS
--    Matches TeamMember[] in mock-data.ts
-- ================================================================

insert into public.users (id, name, email, initials, role, company, plan, timezone, status, joined_at, last_active_at)
values
  ('00000000-0000-0000-0000-000000000001', 'Nadia Khan',   'nadia.khan@acmecorp.com', 'NK', 'owner',   'Acme Corp', 'enterprise', 'America/New_York', 'active',  '2025-09-14T00:00:00Z', now()),
  ('00000000-0000-0000-0000-000000000002', 'Marcus Lee',   'marcus.lee@acmecorp.com', 'ML', 'admin',   'Acme Corp', 'enterprise', 'America/New_York', 'active',  '2025-10-01T00:00:00Z', now() - interval '2 minutes'),
  ('00000000-0000-0000-0000-000000000003', 'Priya Raman',  'priya.r@acmecorp.com',    'PR', 'analyst', 'Acme Corp', 'enterprise', 'Asia/Kolkata',      'active',  '2025-11-15T00:00:00Z', now() - interval '18 minutes'),
  ('00000000-0000-0000-0000-000000000004', 'Jonas Weber',  'jonas.w@acmecorp.com',    'JW', 'analyst', 'Acme Corp', 'enterprise', 'Europe/Berlin',     'active',  '2025-12-03T00:00:00Z', now() - interval '1 hour'),
  ('00000000-0000-0000-0000-000000000005', 'Sofia Alvarez','sofia@acmecorp.com',       'SA', 'viewer',  'Acme Corp', 'enterprise', 'America/Los_Angeles','active', '2026-01-20T00:00:00Z', now() - interval '1 day'),
  ('00000000-0000-0000-0000-000000000006', 'Devon Park',   'devon.park@acmecorp.com', 'DP', 'analyst', 'Acme Corp', 'enterprise', 'America/Chicago',   'invited', '2026-06-01T00:00:00Z', null)
on conflict (id) do update
  set name          = excluded.name,
      role          = excluded.role,
      status        = excluded.status,
      updated_at    = now();


-- ================================================================
-- 2. DEPLOYMENTS
--    Matches DeployEvent[] in mock-data.ts
-- ================================================================

insert into public.deployments (id, version, title, notes, risk, deployed_at, deployed_by)
values
  ('D-001', 'v2.3.7', 'Calendar parser upgrade',      'Bumped ical.js to 2.0',                   'low',    '2026-04-02', '00000000-0000-0000-0000-000000000002'),
  ('D-002', 'v2.3.9', 'Invoice PDF redesign',         'Refactored line-item table layout',        'medium', '2026-04-15', '00000000-0000-0000-0000-000000000002'),
  ('D-003', 'v2.4.0', 'Webhook queue overhaul',       'New retry scheduler',                      'medium', '2026-04-28', '00000000-0000-0000-0000-000000000002'),
  ('D-004', 'v2.4.1', 'Reports performance pass',     'Streamed exports, paginated queries',      'high',   '2026-05-11', '00000000-0000-0000-0000-000000000002'),
  ('D-005', 'v2.4.2', 'Security hardening',           'Cookie SameSite=Strict everywhere',        'high',   '2026-05-20', '00000000-0000-0000-0000-000000000001'),
  ('D-006', 'v2.4.3', 'Mobile push reliability',      'APNs token refresh handler fix',           'low',    '2026-06-01', '00000000-0000-0000-0000-000000000002')
on conflict (id) do update
  set version     = excluded.version,
      title       = excluded.title,
      risk        = excluded.risk,
      deployed_at = excluded.deployed_at,
      updated_at  = now();


-- ================================================================
-- 3. TICKET_CLUSTERS
--    Matches Cluster[] in mock-data.ts
-- ================================================================

insert into public.ticket_clusters (
  id, title, summary, severity, status,
  ticket_count, affected_customers, monthly_cost_usd, confidence,
  root_cause, product_area,
  ticket_trend, example_titles,
  related_deploy_id, first_seen_at, last_seen_at, created_by
)
values
  (
    'CL-1042',
    'Bulk CSV Export Fails Above 500 Rows',
    'Server-side timeout in export pipeline above pagination threshold introduced in v2.4.1.',
    'critical', 'open', 487, 312, 34000.00, 94.00,
    'Worker memory ceiling raised in v2.4.1 truncates stream on large queries.',
    'Exports & Reports',
    '{12,24,41,78,102,134,96,110}',
    '{"Export keeps spinning on 2k row sheet","CSV download returns empty file after 30s","Bulk export timeout on Reports page"}',
    'D-004', '2026-05-14', '2026-06-08',
    '00000000-0000-0000-0000-000000000003'
  ),
  (
    'CL-1039',
    'SSO Re-Auth Loop on Okta Tenants',
    'SAML assertion replay rejected after session cookie refresh — Okta tenants only.',
    'high', 'open', 241, 184, 22500.00, 91.00,
    'Cookie SameSite=Strict toggle ships in v2.4.2 breaks IdP round-trip.',
    'Auth & SSO',
    '{3,8,14,22,31,28,34,29}',
    '{"Stuck on ''Verifying with Okta'' screen","Logged out every 5 minutes","SSO error after Chrome update"}',
    'D-005', '2026-05-22', '2026-06-08',
    '00000000-0000-0000-0000-000000000003'
  ),
  (
    'CL-1037',
    'Invoice PDF Renders With Truncated Line Items',
    'PDF generator clips table cells when invoice has more than 14 lines.',
    'high', 'open', 168, 121, 17800.00, 88.00,
    'Headless renderer fixed-height container introduced in styling refactor.',
    'Billing',
    '{9,11,18,24,22,19,26,31}',
    '{"Invoice missing last 6 items","Customer billed wrong total","PDF cut off mid-row"}',
    'D-002', '2026-04-30', '2026-06-08',
    '00000000-0000-0000-0000-000000000004'
  ),
  (
    'CL-1031',
    'Mobile Push Notifications Silent on iOS 17.4',
    'APNs token rotation skipped after iOS upgrade — notifications delivered silently.',
    'high', 'resolved', 312, 287, 14200.00, 86.00,
    'Token refresh handler bound to deprecated lifecycle event.',
    'Mobile',
    '{22,41,38,49,56,60,71,64}',
    '{"No alerts since iOS update","App badge stuck at 0","Push works only when app open"}',
    null, '2026-04-18', '2026-06-01',
    '00000000-0000-0000-0000-000000000003'
  ),
  (
    'CL-1028',
    'Webhook Retries Storm After 502s',
    'Exponential backoff regression amplifies retries during partial gateway outage.',
    'medium', 'resolved', 96, 54, 9400.00, 79.00,
    'Retry jitter constant set to 0 in queue worker.',
    'Integrations',
    '{4,6,11,18,14,22,19,17}',
    '{"Hit our rate limit from your retries","Duplicate Stripe events","Webhook spam"}',
    'D-003', '2026-05-02', '2026-05-28',
    '00000000-0000-0000-0000-000000000004'
  ),
  (
    'CL-1024',
    'Dashboard Charts Empty on Safari 17',
    'Chart library WebGL fallback fails in Safari due to color profile parsing.',
    'medium', 'open', 142, 119, 6800.00, 82.00,
    'OffscreenCanvas color space mismatch.',
    'Exports & Reports',
    '{8,12,17,21,19,24,28,26}',
    '{"Charts blank in Safari","Have to use Chrome to see data","Reports page broken"}',
    null, '2026-04-26', '2026-06-08',
    '00000000-0000-0000-0000-000000000003'
  ),
  (
    'CL-1019',
    'Search Results Missing Recently Added Records',
    'Search index lag after batch import — 6-12 hour visibility gap.',
    'medium', 'open', 73, 41, 4900.00, 75.00,
    'Indexer worker concurrency reduced for cost optimization.',
    'Search',
    '{2,4,7,9,12,11,14,16}',
    '{"Can''t find contact I added today","Search not indexing","Records invisible"}',
    null, '2026-05-19', '2026-06-08',
    '00000000-0000-0000-0000-000000000004'
  ),
  (
    'CL-1015',
    'Two-Factor Codes Arriving Late via SMS',
    'Twilio short-code throttling in EU region after carrier policy change.',
    'high', 'open', 204, 178, 11600.00, 84.00,
    'Carrier downgraded sender ID to standard throughput tier.',
    'Auth & SSO',
    '{12,18,24,30,28,34,41,38}',
    '{"2FA code came 10 min later","Locked out waiting on SMS","Code expired before received"}',
    null, '2026-05-09', '2026-06-08',
    '00000000-0000-0000-0000-000000000003'
  ),
  (
    'CL-1011',
    'Calendar Sync Drops Recurring Events',
    'ICS parser silently discards events with RRULE exceptions.',
    'low', 'open', 88, 62, 3200.00, 71.00,
    'Parser library upgrade changed RRULE handling.',
    'Integrations',
    '{3,5,4,7,6,9,8,11}',
    '{"Weekly meeting missing","Recurring events disappear","Google Calendar sync broken"}',
    'D-001', '2026-04-11', '2026-06-08',
    '00000000-0000-0000-0000-000000000004'
  )
on conflict (id) do update
  set title             = excluded.title,
      severity          = excluded.severity,
      status            = excluded.status,
      ticket_count      = excluded.ticket_count,
      affected_customers= excluded.affected_customers,
      monthly_cost_usd  = excluded.monthly_cost_usd,
      confidence        = excluded.confidence,
      updated_at        = now();


-- ================================================================
-- 4. TICKETS (sample — 30 representative tickets)
--    In production these are ingested by the pipeline.
--    Embeddings are intentionally null here; the AI pipeline
--    populates them after ingestion.
-- ================================================================

insert into public.tickets (external_id, source, title, body, customer_id, severity, status, channel, related_deploy_id, ticket_created_at)
values
  -- CL-1042: Bulk CSV Export
  ('ZD-88001', 'zendesk', 'Export keeps spinning on 2k row sheet',      'I started a CSV export of our 2000-row contact list and it just spins.',             'CUST-0312', 'critical', 'open',        'email', 'D-004', '2026-05-16T09:12:00Z'),
  ('ZD-88002', 'zendesk', 'CSV download returns empty file after 30s',  'Downloaded the report CSV but the file is empty. Only started after your update.',    'CUST-0087', 'critical', 'open',        'chat',  'D-004', '2026-05-17T11:45:00Z'),
  ('ZD-88003', 'zendesk', 'Bulk export timeout on Reports page',        'Getting a timeout error every time I try to download more than 500 rows.',            'CUST-0219', 'critical', 'open',        'email', 'D-004', '2026-05-18T14:30:00Z'),
  ('ZD-88004', 'zendesk', 'Cannot export quarterly report',             'Our finance team needs the Q2 export but the download fails at 503 rows.',            'CUST-0441', 'critical', 'open',        'email', 'D-004', '2026-05-19T08:00:00Z'),
  ('ZD-88005', 'zendesk', 'CSV export broken for large datasets',       'Works for small datasets but fails consistently above ~500 rows.',                   'CUST-0105', 'high',     'open',        'chat',  'D-004', '2026-05-20T10:22:00Z'),

  -- CL-1039: SSO Re-Auth
  ('ZD-87001', 'zendesk', 'Stuck on Verifying with Okta screen',       'After the recent update I keep getting stuck in the Okta login loop.',                'CUST-0184', 'high',     'open',        'email', 'D-005', '2026-05-22T15:00:00Z'),
  ('ZD-87002', 'zendesk', 'Logged out every 5 minutes',                'Session expires constantly. Happens only on Okta SSO accounts.',                      'CUST-0033', 'high',     'open',        'chat',  'D-005', '2026-05-23T09:30:00Z'),
  ('ZD-87003', 'zendesk', 'SSO error after Chrome update',             'SAML login fails on Chrome 124+. Rolling back Chrome works but that is not viable.',   'CUST-0291', 'high',     'open',        'email', 'D-005', '2026-05-24T11:15:00Z'),
  ('ZD-87004', 'zendesk', 'Okta authentication loop',                  'We are an enterprise Okta tenant. Login works then re-prompts every few minutes.',    'CUST-0172', 'critical', 'open',        'email', 'D-005', '2026-05-25T14:45:00Z'),
  ('ZD-87005', 'zendesk', 'Cannot stay logged in via SSO',             'Our entire team on Okta is affected. Very disruptive to daily operations.',           'CUST-0057', 'high',     'open',        'email', 'D-005', '2026-05-26T08:00:00Z'),

  -- CL-1037: Invoice PDF
  ('ZD-86001', 'zendesk', 'Invoice missing last 6 items',              'Our 20-line invoice is missing the bottom 6 items in the PDF download.',              'CUST-0121', 'high',     'open',        'email', 'D-002', '2026-05-02T10:00:00Z'),
  ('ZD-86002', 'zendesk', 'Customer billed wrong total',               'Invoice PDF shows $1,200 but the portal total is $2,800. Line items cut off.',        'CUST-0088', 'critical', 'open',        'email', 'D-002', '2026-05-03T12:30:00Z'),
  ('ZD-86003', 'zendesk', 'PDF cut off mid-row',                       'Last row of the invoice table is cut in half. Looks unprofessional to customers.',    'CUST-0044', 'high',     'open',        'email', 'D-002', '2026-05-04T09:15:00Z'),

  -- CL-1031: Mobile Push
  ('ZD-85001', 'zendesk', 'No alerts since iOS update',                'Upgraded to iOS 17.4 last week. Zero push notifications since then.',                 'CUST-0287', 'high',     'resolved',    'chat',  null,    '2026-04-19T08:00:00Z'),
  ('ZD-85002', 'zendesk', 'App badge stuck at 0',                      'Badge counter never updates. Checked all notification settings — they are on.',       'CUST-0098', 'medium',   'resolved',    'chat',  null,    '2026-04-20T11:00:00Z'),
  ('ZD-85003', 'zendesk', 'Push works only when app open',             'Notifications only arrive if I have the app in the foreground. Silent otherwise.',    'CUST-0155', 'high',     'resolved',    'email', null,    '2026-04-21T14:00:00Z'),

  -- CL-1028: Webhook Retries
  ('ZD-84001', 'zendesk', 'Hit our rate limit from your retries',      'Your webhooks are hitting our endpoint 50+ times for a single event.',                'CUST-0054', 'high',     'resolved',    'email', 'D-003', '2026-05-03T10:00:00Z'),
  ('ZD-84002', 'zendesk', 'Duplicate Stripe events',                   'Receiving duplicate payment.succeeded events. This is causing double-processing.',    'CUST-0021', 'critical', 'resolved',    'email', 'D-003', '2026-05-04T09:30:00Z'),
  ('ZD-84003', 'zendesk', 'Webhook spam',                              'Our Slack channel is flooded with duplicate FixLoop webhook notifications.',          'CUST-0037', 'medium',   'resolved',    'chat',  'D-003', '2026-05-05T15:00:00Z'),

  -- CL-1024: Safari Charts
  ('ZD-83001', 'zendesk', 'Charts blank in Safari',                    'All the charts on the dashboard are completely blank. Only in Safari 17.',            'CUST-0119', 'medium',   'open',        'chat',  null,    '2026-04-27T09:00:00Z'),
  ('ZD-83002', 'zendesk', 'Have to use Chrome to see data',            'Dashboard works in Chrome but all charts disappear in Safari. Please fix.',          'CUST-0072', 'medium',   'open',        'email', null,    '2026-04-28T11:30:00Z'),
  ('ZD-83003', 'zendesk', 'Reports page broken in Safari',             'Revenue and volume charts not rendering. Safari 17.4 on macOS 14.',                  'CUST-0048', 'medium',   'open',        'email', null,    '2026-04-29T14:00:00Z'),

  -- CL-1019: Search
  ('ZD-82001', 'zendesk', 'Can''t find contact I added today',         'Added a new contact an hour ago but search returns nothing. Very frustrating.',       'CUST-0041', 'medium',   'open',        'chat',  null,    '2026-05-20T10:00:00Z'),
  ('ZD-82002', 'zendesk', 'Search not indexing new records',           'Recently imported 500 contacts via CSV. None appear in search results.',             'CUST-0019', 'high',     'open',        'email', null,    '2026-05-21T08:30:00Z'),

  -- CL-1015: 2FA SMS
  ('ZD-81001', 'zendesk', '2FA code came 10 min later',                'The SMS verification code arrived 10 minutes late. I had already given up.',         'CUST-0178', 'high',     'open',        'email', null,    '2026-05-10T09:00:00Z'),
  ('ZD-81002', 'zendesk', 'Locked out waiting on SMS',                 'I can''t log in because the 2FA code never arrives. This is blocking my work.',     'CUST-0091', 'high',     'open',        'chat',  null,    '2026-05-11T10:30:00Z'),
  ('ZD-81003', 'zendesk', 'Code expired before received',              'By the time the SMS code arrives the 5-minute window has expired.',                  'CUST-0143', 'medium',   'open',        'email', null,    '2026-05-12T14:00:00Z'),

  -- CL-1011: Calendar Sync
  ('ZD-80001', 'zendesk', 'Weekly meeting missing from calendar',      'My recurring Monday standup disappeared after syncing with Google Calendar.',         'CUST-0062', 'low',      'open',        'email', 'D-001', '2026-04-12T09:00:00Z'),
  ('ZD-80002', 'zendesk', 'Recurring events disappear after sync',     'Any event with a recurrence rule is dropped when I sync with Apple Calendar.',       'CUST-0027', 'low',      'open',        'chat',  'D-001', '2026-04-13T11:00:00Z'),
  ('ZD-80003', 'zendesk', 'Google Calendar sync broken for repeating', 'Imported an ICS file. All one-off events imported fine but repeating events missing.','CUST-0014', 'medium',  'open',        'email', 'D-001', '2026-04-14T14:00:00Z')
on conflict (external_id) do nothing;


-- ================================================================
-- 5. CLUSTER_TICKETS  (junction mapping)
--    Map the 30 seeded tickets to their clusters.
-- ================================================================

-- Resolve ticket IDs by external_id and link to clusters
do $$
declare
  mapping record;
begin
  for mapping in
    select external_id, cluster_id
    from (values
      ('ZD-88001', 'CL-1042'), ('ZD-88002', 'CL-1042'), ('ZD-88003', 'CL-1042'), ('ZD-88004', 'CL-1042'), ('ZD-88005', 'CL-1042'),
      ('ZD-87001', 'CL-1039'), ('ZD-87002', 'CL-1039'), ('ZD-87003', 'CL-1039'), ('ZD-87004', 'CL-1039'), ('ZD-87005', 'CL-1039'),
      ('ZD-86001', 'CL-1037'), ('ZD-86002', 'CL-1037'), ('ZD-86003', 'CL-1037'),
      ('ZD-85001', 'CL-1031'), ('ZD-85002', 'CL-1031'), ('ZD-85003', 'CL-1031'),
      ('ZD-84001', 'CL-1028'), ('ZD-84002', 'CL-1028'), ('ZD-84003', 'CL-1028'),
      ('ZD-83001', 'CL-1024'), ('ZD-83002', 'CL-1024'), ('ZD-83003', 'CL-1024'),
      ('ZD-82001', 'CL-1019'), ('ZD-82002', 'CL-1019'),
      ('ZD-81001', 'CL-1015'), ('ZD-81002', 'CL-1015'), ('ZD-81003', 'CL-1015'),
      ('ZD-80001', 'CL-1011'), ('ZD-80002', 'CL-1011'), ('ZD-80003', 'CL-1011')
    ) as t(external_id, cluster_id)
  loop
    insert into public.cluster_tickets (cluster_id, ticket_id, similarity)
    select mapping.cluster_id, t.id, 0.9000
    from public.tickets t
    where t.external_id = mapping.external_id
    on conflict do nothing;
  end loop;
end
$$;


-- ================================================================
-- 6. INVESTIGATIONS
--    Matches AIInvestigation[] in mock-data.ts
-- ================================================================

insert into public.investigations (
  id, cluster_id, root_cause, confidence, impact_level,
  affected_customers, revenue_impact_usd,
  deploy_correlation_id, deploy_correlation_score,
  reasoning_steps,
  sim_before_ticket_count, sim_after_ticket_count, sim_deflection_pct, sim_recovered_usd,
  model_version, created_by, approved_by, approved_at
)
values
  (
    'AI-7741', 'CL-1042', 'Bulk CSV Export Failure', 94.00, 'critical',
    312, 34000.00,
    'D-004', 0.9400,
    '{
      "Ticket volume rose 412% within 36h of v2.4.1 deploy.",
      "97% of tickets reference exports above ~500 rows.",
      "All affected accounts share the streamed-export feature flag.",
      "No correlation with any third-party provider incident in the same window."
    }',
    487, 43, 91.00, 31000.00,
    'fixloop-reasoner-v3',
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000001',
    '2026-06-08T08:00:00Z'
  ),
  (
    'AI-7728', 'CL-1039', 'Okta SAML cookie scoping regression', 91.00, 'high',
    184, 22500.00,
    'D-005', 0.9100,
    '{
      "100% of impacted tenants use Okta as IdP.",
      "Spike starts within 14 minutes of v2.4.2 rollout.",
      "Browser instrumentation shows cookie missing on /sso/callback round-trip."
    }',
    241, 29, 88.00, 19800.00,
    'fixloop-reasoner-v3',
    '00000000-0000-0000-0000-000000000003',
    null,
    null
  )
on conflict (id) do update
  set confidence    = excluded.confidence,
      approved_by   = excluded.approved_by,
      approved_at   = excluded.approved_at,
      updated_at    = now();


-- ================================================================
-- 7. INVESTIGATION_EVIDENCE
--    Matches Evidence[] arrays in mock-data.ts
-- ================================================================

insert into public.investigation_evidence (id, investigation_id, evidence_type, title, detail, weight, sort_order)
values
  -- AI-7741 evidence
  ('AI-7741-E-1', 'AI-7741', 'deploy_correlation', 'Deploy v2.4.1 — Export Service Rewrite',
   'Worker memory ceiling lowered from 2GB to 768MB. Stream chunking changed from 250 to 1000 rows.',
   0.9400, 1),
  ('AI-7741-E-2', 'AI-7741', 'ticket_pattern', '487 tickets, single semantic cluster',
   'Keywords: ''spinning'', ''empty CSV'', ''timeout'', ''30s''. 91% sentiment negative.',
   0.8800, 2),
  ('AI-7741-E-3', 'AI-7741', 'customer_impact', '312 customers — 41 enterprise',
   'Includes 6 of top-10 ARR accounts. Renewal risk flag triggered on 4.',
   0.8200, 3),
  ('AI-7741-E-4', 'AI-7741', 'similar_ticket', 'Q4 2025 analogue (CL-0871)',
   'Same root cause pattern after v2.1.3 stream refactor — resolved by reverting chunk size.',
   0.7100, 4),

  -- AI-7728 evidence
  ('AI-7728-E-1', 'AI-7728', 'deploy_correlation', 'Deploy v2.4.2 — SameSite=Strict',
   'Hardening pass flipped SameSite to Strict for all auth cookies.',
   0.9100, 1),
  ('AI-7728-E-2', 'AI-7728', 'ticket_pattern', '241 tickets, Okta-only',
   '''Verifying with Okta'' loop, ''5 minute logouts'', SAML replay errors.',
   0.8600, 2),
  ('AI-7728-E-3', 'AI-7728', 'customer_impact', '184 customers — Okta tenants',
   'Cross-domain IdP round-trip drops cookie.',
   0.7800, 3)
on conflict (id) do nothing;


-- ================================================================
-- 8. FIX_RECOMMENDATIONS
--    Matches Resolution[] in mock-data.ts
-- ================================================================

insert into public.fix_recommendations (
  id, cluster_id, investigation_id,
  title, description,
  owner_name, owner_user_id, status,
  expected_reduction_pct, expected_recovery_usd,
  actual_reduction_pct, actual_recovery_usd,
  before_ticket_count, after_ticket_count,
  estimated_eta, created_by, resolved_by, resolved_at
)
values
  (
    'R-1', 'CL-1042', 'AI-7741',
    'Re-enable streamed worker output and revert chunking',
    'Restore 1.5GB memory ceiling on export workers, revert to 250-row chunked pagination, and add a regression test for >2k row exports.',
    'Platform Squad', '00000000-0000-0000-0000-000000000003',
    'in_progress',
    91.00, 31000.00, null, null,
    null, null,
    '2 days',
    '00000000-0000-0000-0000-000000000003', null, null
  ),
  (
    'R-2', 'CL-1028', 'AI-7728',
    'Restore jitter and cap retries',
    'Restore full-jitter (max 30s) on the webhook retry queue and cap total retries at 6.',
    'Integrations', '00000000-0000-0000-0000-000000000004',
    'resolved',
    78.00, 8200.00, 78.00, 8200.00,
    96, 21,
    '1 day',
    '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0000-000000000004',
    '2026-05-29T12:00:00Z'
  ),
  (
    'R-3', 'CL-1039', 'AI-7728',
    'Scope SameSite=Lax for IdP callback domain',
    'Apply SameSite=Lax only on /sso/* routes. Keep Strict on app cookies.',
    'Identity', '00000000-0000-0000-0000-000000000002',
    'in_progress',
    88.00, 19800.00, null, null,
    null, null,
    '1 day',
    '00000000-0000-0000-0000-000000000002', null, null
  ),
  (
    'R-4', 'CL-1024', null,
    'Force sRGB profile in canvas fallback for Safari user agents',
    'Force sRGB profile in canvas fallback for Safari user agents.',
    'Frontend', '00000000-0000-0000-0000-000000000003',
    'open',
    95.00, 6500.00, null, null,
    null, null,
    '3 days',
    '00000000-0000-0000-0000-000000000003', null, null
  ),
  (
    'R-5', 'CL-1031', null,
    'Rebind APNs refresh to applicationDidBecomeActive',
    'Rebind APNs token refresh to the applicationDidBecomeActive lifecycle event and force re-send of all tokens.',
    'Mobile', '00000000-0000-0000-0000-000000000004',
    'resolved',
    92.00, 13100.00, 92.00, 13100.00,
    312, 24,
    '2 days',
    '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0000-000000000004',
    '2026-06-02T10:00:00Z'
  )
on conflict (id) do update
  set status              = excluded.status,
      actual_reduction_pct = excluded.actual_reduction_pct,
      actual_recovery_usd  = excluded.actual_recovery_usd,
      resolved_by          = excluded.resolved_by,
      resolved_at          = excluded.resolved_at,
      updated_at           = now();


-- ================================================================
-- 9. VALIDATION_RESULTS
--    Before/after measurements for resolved fixes (R-2, R-5)
-- ================================================================

insert into public.validation_results (fix_recommendation_id, measurement_date, period_label, ticket_count, deflection_pct, revenue_recovered_usd, notes, measured_by)
values
  -- R-2 Webhook fix measurements
  ('R-2', '2026-05-20', 'Baseline (pre-fix)',      96, null,  null,    'Baseline before jitter fix deployed.',              '00000000-0000-0000-0000-000000000004'),
  ('R-2', '2026-05-25', 'Week 1 post-ship',        48, 50.00, 4100.00, 'Significant drop in first week after deploy.',       '00000000-0000-0000-0000-000000000004'),
  ('R-2', '2026-06-01', 'Week 2 post-ship',        21, 78.00, 8200.00, 'Stabilised at target deflection rate. Loop closed.', '00000000-0000-0000-0000-000000000004'),

  -- R-5 Mobile push fix measurements
  ('R-5', '2026-04-20', 'Baseline (pre-fix)',      312, null,  null,    'APNs token refresh issue confirmed on iOS 17.4.',    '00000000-0000-0000-0000-000000000004'),
  ('R-5', '2026-06-03', 'Post-ship Day 2',          62, 80.00, 10480.00,'v2.4.3 shipped. Most tickets resolved immediately.', '00000000-0000-0000-0000-000000000004'),
  ('R-5', '2026-06-05', 'Post-ship Day 4 (final)',  24, 92.00, 13100.00,'Confirmed: push notifications working on iOS 17.4.', '00000000-0000-0000-0000-000000000004')
on conflict do nothing;


-- ================================================================
-- 10. REPORTS
--     Q2 2026 executive summary (matches executiveSummary in mock-data.ts)
-- ================================================================

insert into public.reports (
  report_type, title, quarter, date_from, date_to,
  cluster_ids, total_tickets, active_clusters,
  revenue_at_risk_usd, revenue_recovered_usd, deflection_rate,
  summary_html, created_by
)
values
  (
    'executive_summary',
    'Q2 2026 Product Intelligence Report',
    'Q2 2026',
    '2026-04-01',
    '2026-06-30',
    '{CL-1042,CL-1039,CL-1037,CL-1031,CL-1028,CL-1024,CL-1019,CL-1015,CL-1011}',
    12480, 9,
    340000.00, 211000.00, 0.7400,
    '<p>In Q2 2026, FixLoop AI analyzed <strong>12,480</strong> support tickets and surfaced <strong>9</strong> active root-cause clusters representing <strong>$340k</strong> in revenue at risk.</p><p>Verified fixes shipped this quarter recovered <strong>$211k</strong> with an aggregate deflection rate of <strong>74%</strong>. The remaining backlog is concentrated in authentication and reporting, with deploys v2.4.1 and v2.4.2 identified as causal events.</p>',
    '00000000-0000-0000-0000-000000000001'
  )
on conflict do nothing;


-- ================================================================
-- VERIFY (optional — comment out in production CI)
-- ================================================================

select 'users'                  as tbl, count(*) from public.users                  union all
select 'deployments',                   count(*) from public.deployments             union all
select 'tickets',                       count(*) from public.tickets                 union all
select 'ticket_clusters',               count(*) from public.ticket_clusters         union all
select 'cluster_tickets',               count(*) from public.cluster_tickets         union all
select 'investigations',                count(*) from public.investigations          union all
select 'investigation_evidence',        count(*) from public.investigation_evidence  union all
select 'fix_recommendations',           count(*) from public.fix_recommendations     union all
select 'validation_results',            count(*) from public.validation_results      union all
select 'reports',                       count(*) from public.reports
order by tbl;
