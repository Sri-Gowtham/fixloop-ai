export type Severity = "critical" | "high" | "medium" | "low";
export type Status = "open" | "in_progress" | "resolved";

export interface Cluster {
  id: string;
  title: string;
  summary: string;
  ticketCount: number;
  severity: Severity;
  monthlyCost: number;
  confidence: number;
  affectedCustomers: number;
  firstSeen: string;
  trend: number[];
  examples: string[];
  rootCause: string;
  relatedDeploy?: string;
}

export const clusters: Cluster[] = [
  {
    id: "CL-1042",
    title: "Bulk CSV Export Fails Above 500 Rows",
    summary: "Server-side timeout in export pipeline above pagination threshold introduced in v2.4.1.",
    ticketCount: 487,
    severity: "critical",
    monthlyCost: 34000,
    confidence: 94,
    affectedCustomers: 312,
    firstSeen: "2026-05-14",
    trend: [12, 24, 41, 78, 102, 134, 96, 110],
    examples: [
      "Export keeps spinning on 2k row sheet",
      "CSV download returns empty file after 30s",
      "Bulk export timeout on Reports page",
    ],
    rootCause: "Worker memory ceiling raised in v2.4.1 truncates stream on large queries.",
    relatedDeploy: "v2.4.1",
  },
  {
    id: "CL-1039",
    title: "SSO Re-Auth Loop on Okta Tenants",
    summary: "SAML assertion replay rejected after session cookie refresh — Okta tenants only.",
    ticketCount: 241,
    severity: "high",
    monthlyCost: 22500,
    confidence: 91,
    affectedCustomers: 184,
    firstSeen: "2026-05-22",
    trend: [3, 8, 14, 22, 31, 28, 34, 29],
    examples: [
      "Stuck on 'Verifying with Okta' screen",
      "Logged out every 5 minutes",
      "SSO error after Chrome update",
    ],
    rootCause: "Cookie SameSite=Strict toggle ships in v2.4.2 breaks IdP round-trip.",
    relatedDeploy: "v2.4.2",
  },
  {
    id: "CL-1037",
    title: "Invoice PDF Renders With Truncated Line Items",
    summary: "PDF generator clips table cells when invoice has more than 14 lines.",
    ticketCount: 168,
    severity: "high",
    monthlyCost: 17800,
    confidence: 88,
    affectedCustomers: 121,
    firstSeen: "2026-04-30",
    trend: [9, 11, 18, 24, 22, 19, 26, 31],
    examples: ["Invoice missing last 6 items", "Customer billed wrong total", "PDF cut off mid-row"],
    rootCause: "Headless renderer fixed-height container introduced in styling refactor.",
    relatedDeploy: "v2.3.9",
  },
  {
    id: "CL-1031",
    title: "Mobile Push Notifications Silent on iOS 17.4",
    summary: "APNs token rotation skipped after iOS upgrade — notifications delivered silently.",
    ticketCount: 312,
    severity: "high",
    monthlyCost: 14200,
    confidence: 86,
    affectedCustomers: 287,
    firstSeen: "2026-04-18",
    trend: [22, 41, 38, 49, 56, 60, 71, 64],
    examples: ["No alerts since iOS update", "App badge stuck at 0", "Push works only when app open"],
    rootCause: "Token refresh handler bound to deprecated lifecycle event.",
  },
  {
    id: "CL-1028",
    title: "Webhook Retries Storm After 502s",
    summary: "Exponential backoff regression amplifies retries during partial gateway outage.",
    ticketCount: 96,
    severity: "medium",
    monthlyCost: 9400,
    confidence: 79,
    affectedCustomers: 54,
    firstSeen: "2026-05-02",
    trend: [4, 6, 11, 18, 14, 22, 19, 17],
    examples: ["Hit our rate limit from your retries", "Duplicate Stripe events", "Webhook spam"],
    rootCause: "Retry jitter constant set to 0 in queue worker.",
    relatedDeploy: "v2.4.0",
  },
  {
    id: "CL-1024",
    title: "Dashboard Charts Empty on Safari 17",
    summary: "Chart library WebGL fallback fails in Safari due to color profile parsing.",
    ticketCount: 142,
    severity: "medium",
    monthlyCost: 6800,
    confidence: 82,
    affectedCustomers: 119,
    firstSeen: "2026-04-26",
    trend: [8, 12, 17, 21, 19, 24, 28, 26],
    examples: ["Charts blank in Safari", "Have to use Chrome to see data", "Reports page broken"],
    rootCause: "OffscreenCanvas color space mismatch.",
  },
  {
    id: "CL-1019",
    title: "Search Results Missing Recently Added Records",
    summary: "Search index lag after batch import — 6-12 hour visibility gap.",
    ticketCount: 73,
    severity: "medium",
    monthlyCost: 4900,
    confidence: 75,
    affectedCustomers: 41,
    firstSeen: "2026-05-19",
    trend: [2, 4, 7, 9, 12, 11, 14, 16],
    examples: ["Can't find contact I added today", "Search not indexing", "Records invisible"],
    rootCause: "Indexer worker concurrency reduced for cost optimization.",
  },
  {
    id: "CL-1015",
    title: "Two-Factor Codes Arriving Late via SMS",
    summary: "Twilio short-code throttling in EU region after carrier policy change.",
    ticketCount: 204,
    severity: "high",
    monthlyCost: 11600,
    confidence: 84,
    affectedCustomers: 178,
    firstSeen: "2026-05-09",
    trend: [12, 18, 24, 30, 28, 34, 41, 38],
    examples: ["2FA code came 10 min later", "Locked out waiting on SMS", "Code expired before received"],
    rootCause: "Carrier downgraded sender ID to standard throughput tier.",
  },
  {
    id: "CL-1011",
    title: "Calendar Sync Drops Recurring Events",
    summary: "ICS parser silently discards events with RRULE exceptions.",
    ticketCount: 88,
    severity: "low",
    monthlyCost: 3200,
    confidence: 71,
    affectedCustomers: 62,
    firstSeen: "2026-04-11",
    trend: [3, 5, 4, 7, 6, 9, 8, 11],
    examples: ["Weekly meeting missing", "Recurring events disappear", "Google Calendar sync broken"],
    rootCause: "Parser library upgrade changed RRULE handling.",
    relatedDeploy: "v2.3.7",
  },
];

export interface DeployEvent {
  id: string;
  date: string;
  version: string;
  title: string;
  notes: string;
  risk: Severity;
}

export const deploys: DeployEvent[] = [
  { id: "D-001", date: "2026-04-02", version: "v2.3.7", title: "Calendar parser upgrade", notes: "Bumped ical.js to 2.0", risk: "low" },
  { id: "D-002", date: "2026-04-15", version: "v2.3.9", title: "Invoice PDF redesign", notes: "Refactored line-item table layout", risk: "medium" },
  { id: "D-003", date: "2026-04-28", version: "v2.4.0", title: "Webhook queue overhaul", notes: "New retry scheduler", risk: "medium" },
  { id: "D-004", date: "2026-05-11", version: "v2.4.1", title: "Reports performance pass", notes: "Streamed exports, paginated queries", risk: "high" },
  { id: "D-005", date: "2026-05-20", version: "v2.4.2", title: "Security hardening", notes: "Cookie SameSite=Strict everywhere", risk: "high" },
  { id: "D-006", date: "2026-06-01", version: "v2.4.3", title: "Mobile push reliability", notes: "APNs token refresh handler fix", risk: "low" },
];

export const productHealthScore = 72;

export const ticketVolumeTrend = [
  { day: "Mon", tickets: 142, resolved: 118 },
  { day: "Tue", tickets: 168, resolved: 131 },
  { day: "Wed", tickets: 201, resolved: 154 },
  { day: "Thu", tickets: 247, resolved: 178 },
  { day: "Fri", tickets: 289, resolved: 209 },
  { day: "Sat", tickets: 134, resolved: 124 },
  { day: "Sun", tickets: 98, resolved: 91 },
];

export const revenueImpact = [
  { month: "Jan", atRisk: 180, recovered: 40 },
  { month: "Feb", atRisk: 220, recovered: 70 },
  { month: "Mar", atRisk: 260, recovered: 110 },
  { month: "Apr", atRisk: 310, recovered: 160 },
  { month: "May", atRisk: 340, recovered: 210 },
  { month: "Jun", atRisk: 305, recovered: 260 },
];

export const clusterDistribution = [
  { name: "Auth & SSO", value: 28, color: "var(--critical)" },
  { name: "Exports & Reports", value: 24, color: "var(--primary)" },
  { name: "Billing", value: 18, color: "var(--warning)" },
  { name: "Mobile", value: 16, color: "var(--secondary)" },
  { name: "Integrations", value: 14, color: "var(--chart-5)" },
];

export const rootCauseHeatmap: { area: string; values: number[] }[] = [
  { area: "Auth", values: [4, 9, 12, 18, 22, 14, 8] },
  { area: "Billing", values: [2, 5, 8, 11, 9, 6, 4] },
  { area: "Exports", values: [6, 11, 17, 24, 31, 28, 19] },
  { area: "Mobile", values: [3, 7, 10, 13, 16, 12, 9] },
  { area: "Webhooks", values: [1, 3, 5, 7, 6, 4, 3] },
  { area: "Search", values: [2, 4, 6, 8, 7, 5, 3] },
];

export interface Alert {
  id: string;
  title: string;
  detail: string;
  severity: Severity;
  time: string;
}

export const recentAlerts: Alert[] = [
  { id: "A-1", title: "New cluster crossed 400 tickets", detail: "Bulk CSV Export Fails Above 500 Rows", severity: "critical", time: "12m ago" },
  { id: "A-2", title: "Correlation found", detail: "Deploy v2.4.2 ↔ SSO Re-Auth Loop (91%)", severity: "high", time: "1h ago" },
  { id: "A-3", title: "Deflection verified", detail: "Webhook Retries Storm down 78% post-fix", severity: "low", time: "3h ago" },
  { id: "A-4", title: "Revenue at risk threshold", detail: "Total exceeded $300k for May", severity: "high", time: "6h ago" },
  { id: "A-5", title: "Spike detected", detail: "2FA Codes Arriving Late +42% in 24h", severity: "medium", time: "9h ago" },
];

export interface Resolution {
  id: string;
  clusterId: string;
  issue: string;
  fix: string;
  status: Status;
  expectedReduction: number;
  costRecovery: number;
  owner: string;
  before?: number;
  after?: number;
}

export const resolutions: Resolution[] = [
  {
    id: "R-1",
    clusterId: "CL-1042",
    issue: "Bulk CSV Export Fails Above 500 Rows",
    fix: "Re-enable streamed worker output, raise memory ceiling to 1.5GB, paginate at 250 rows.",
    status: "in_progress",
    expectedReduction: 91,
    costRecovery: 31000,
    owner: "Platform Squad",
  },
  {
    id: "R-2",
    clusterId: "CL-1028",
    issue: "Webhook Retries Storm After 502s",
    fix: "Restore jitter (full-jitter, max 30s) and cap retries at 6.",
    status: "resolved",
    expectedReduction: 78,
    costRecovery: 8200,
    owner: "Integrations",
    before: 96,
    after: 21,
  },
  {
    id: "R-3",
    clusterId: "CL-1039",
    issue: "SSO Re-Auth Loop on Okta Tenants",
    fix: "Set SameSite=Lax for IdP callback domain; ship cookie scoping fix.",
    status: "in_progress",
    expectedReduction: 88,
    costRecovery: 19800,
    owner: "Identity",
  },
  {
    id: "R-4",
    clusterId: "CL-1024",
    issue: "Dashboard Charts Empty on Safari 17",
    fix: "Force sRGB profile in canvas fallback for Safari user agents.",
    status: "open",
    expectedReduction: 95,
    costRecovery: 6500,
    owner: "Frontend",
  },
  {
    id: "R-5",
    clusterId: "CL-1031",
    issue: "Mobile Push Notifications Silent on iOS 17.4",
    fix: "Rebind APNs refresh to applicationDidBecomeActive; resend tokens.",
    status: "resolved",
    expectedReduction: 92,
    costRecovery: 13100,
    owner: "Mobile",
    before: 312,
    after: 24,
  },
];

export const executiveSummary = {
  quarter: "Q2 2026",
  totalTickets: 12480,
  activeClusters: 9,
  revenueAtRisk: 340000,
  revenueRecovered: 211000,
  deflectionRate: 0.74,
  topIssues: clusters.slice(0, 5),
  priorities: [
    { rank: 1, cluster: "CL-1042", reason: "Highest revenue impact, enterprise accounts affected", action: "Ship streamed export hotfix this week" },
    { rank: 2, cluster: "CL-1039", reason: "Authentication friction across Okta accounts", action: "Roll back SameSite change for IdP routes" },
    { rank: 3, cluster: "CL-1015", reason: "Account lockouts driving churn signals", action: "Provision EU short code; enable WhatsApp fallback" },
    { rank: 4, cluster: "CL-1031", reason: "Mobile engagement decline", action: "Confirm rollout of v2.4.3 push fix" },
    { rank: 5, cluster: "CL-1037", reason: "Customer-visible billing errors", action: "Switch invoice renderer to auto-height layout" },
  ],
};

// ============= AI Command Center =============

export interface Evidence {
  id: string;
  type: "ticket_pattern" | "deploy_correlation" | "customer_impact" | "similar_ticket";
  title: string;
  detail: string;
  weight: number;
}

export interface AIInvestigation {
  id: string;
  clusterId: string;
  rootCause: string;
  confidence: number;
  impactLevel: Severity;
  affectedCustomers: number;
  revenueImpact: number;
  deployCorrelation: { version: string; date: string; correlation: number };
  reasoning: string[];
  evidence: Evidence[];
  recommendation: {
    title: string;
    detail: string;
    owner: string;
    expectedReduction: number;
    expectedRecovery: number;
    eta: string;
  };
  simulation: { before: number; after: number; deflection: number; recovered: number };
}

export const aiInvestigations: AIInvestigation[] = [
  {
    id: "AI-7741",
    clusterId: "CL-1042",
    rootCause: "Bulk CSV Export Failure",
    confidence: 94,
    impactLevel: "critical",
    affectedCustomers: 312,
    revenueImpact: 34000,
    deployCorrelation: { version: "v2.4.1", date: "2026-05-11", correlation: 0.94 },
    reasoning: [
      "Ticket volume rose 412% within 36h of v2.4.1 deploy.",
      "97% of tickets reference exports above ~500 rows.",
      "All affected accounts share the streamed-export feature flag.",
      "No correlation with any third-party provider incident in the same window.",
    ],
    evidence: [
      { id: "E-1", type: "deploy_correlation", title: "Deploy v2.4.1 — Export Service Rewrite", detail: "Worker memory ceiling lowered from 2GB to 768MB. Stream chunking changed from 250 to 1000 rows.", weight: 0.94 },
      { id: "E-2", type: "ticket_pattern", title: "487 tickets, single semantic cluster", detail: "Keywords: 'spinning', 'empty CSV', 'timeout', '30s'. 91% sentiment negative.", weight: 0.88 },
      { id: "E-3", type: "customer_impact", title: "312 customers — 41 enterprise", detail: "Includes 6 of top-10 ARR accounts. Renewal risk flag triggered on 4.", weight: 0.82 },
      { id: "E-4", type: "similar_ticket", title: "Q4 2025 analogue (CL-0871)", detail: "Same root cause pattern after v2.1.3 stream refactor — resolved by reverting chunk size.", weight: 0.71 },
    ],
    recommendation: {
      title: "Re-enable streamed worker output and revert chunking",
      detail: "Restore 1.5GB memory ceiling on export workers, revert to 250-row chunked pagination, and add a regression test for >2k row exports.",
      owner: "Platform Squad — N. Alvarez",
      expectedReduction: 91,
      expectedRecovery: 31000,
      eta: "2 days",
    },
    simulation: { before: 487, after: 43, deflection: 91, recovered: 31000 },
  },
  {
    id: "AI-7728",
    clusterId: "CL-1039",
    rootCause: "Okta SAML cookie scoping regression",
    confidence: 91,
    impactLevel: "high",
    affectedCustomers: 184,
    revenueImpact: 22500,
    deployCorrelation: { version: "v2.4.2", date: "2026-05-20", correlation: 0.91 },
    reasoning: [
      "100% of impacted tenants use Okta as IdP.",
      "Spike starts within 14 minutes of v2.4.2 rollout.",
      "Browser instrumentation shows cookie missing on /sso/callback round-trip.",
    ],
    evidence: [
      { id: "E-1", type: "deploy_correlation", title: "Deploy v2.4.2 — SameSite=Strict", detail: "Hardening pass flipped SameSite to Strict for all auth cookies.", weight: 0.91 },
      { id: "E-2", type: "ticket_pattern", title: "241 tickets, Okta-only", detail: "'Verifying with Okta' loop, '5 minute logouts', SAML replay errors.", weight: 0.86 },
      { id: "E-3", type: "customer_impact", title: "184 customers — Okta tenants", detail: "Cross-domain IdP round-trip drops cookie.", weight: 0.78 },
    ],
    recommendation: {
      title: "Scope SameSite=Lax for IdP callback domain",
      detail: "Apply SameSite=Lax only on /sso/* routes. Keep Strict on app cookies.",
      owner: "Identity — R. Mehta",
      expectedReduction: 88,
      expectedRecovery: 19800,
      eta: "1 day",
    },
    simulation: { before: 241, after: 29, deflection: 88, recovered: 19800 },
  },
];

export const copilotSuggestions = [
  "Why is this cluster critical?",
  "Which deployment caused this issue?",
  "Generate Jira ticket from this investigation",
  "Show evidence for the root cause",
  "Summarize impact for the executive report",
  "What's the expected revenue recovery?",
];

// ============= Users / Team / Integrations =============

export interface UserProfile {
  name: string;
  initials: string;
  role: string;
  email: string;
  company: string;
  plan: string;
  timezone: string;
  joined: string;
}

export const currentUser: UserProfile = {
  name: "Nadia Khan",
  initials: "NK",
  role: "VP, Product Operations",
  email: "nadia.khan@acmecorp.com",
  company: "Acme Corp",
  plan: "Enterprise",
  timezone: "America/New_York",
  joined: "2025-09-14",
};

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: "Owner" | "Admin" | "Analyst" | "Viewer";
  status: "active" | "invited";
  lastActive: string;
}

export const teamMembers: TeamMember[] = [
  { id: "U-1", name: "Nadia Khan", email: "nadia.khan@acmecorp.com", role: "Owner", status: "active", lastActive: "Just now" },
  { id: "U-2", name: "Marcus Lee", email: "marcus.lee@acmecorp.com", role: "Admin", status: "active", lastActive: "2m ago" },
  { id: "U-3", name: "Priya Raman", email: "priya.r@acmecorp.com", role: "Analyst", status: "active", lastActive: "18m ago" },
  { id: "U-4", name: "Jonas Weber", email: "jonas.w@acmecorp.com", role: "Analyst", status: "active", lastActive: "1h ago" },
  { id: "U-5", name: "Sofia Alvarez", email: "sofia@acmecorp.com", role: "Viewer", status: "active", lastActive: "Yesterday" },
  { id: "U-6", name: "devon.park@acmecorp.com", email: "devon.park@acmecorp.com", role: "Analyst", status: "invited", lastActive: "Pending" },
];

export interface Integration {
  id: string;
  name: string;
  category: "Support" | "Issues" | "Comms" | "Source";
  description: string;
  status: "connected" | "disconnected" | "error";
  lastSync?: string;
  records?: number;
}

export const integrations: Integration[] = [
  { id: "INT-1", name: "Zendesk", category: "Support", description: "Ingest support tickets, macros, satisfaction.", status: "connected", lastSync: "2m ago", records: 12480 },
  { id: "INT-2", name: "Jira", category: "Issues", description: "Push fix tickets and sync resolution status.", status: "connected", lastSync: "4m ago", records: 318 },
  { id: "INT-3", name: "Slack", category: "Comms", description: "Post cluster alerts and resolution updates.", status: "connected", lastSync: "1m ago" },
  { id: "INT-4", name: "GitHub", category: "Source", description: "Correlate deploys, PRs, and rollbacks to clusters.", status: "connected", lastSync: "6m ago", records: 612 },
  { id: "INT-5", name: "Intercom", category: "Support", description: "Pull conversations and customer fit signals.", status: "disconnected" },
  { id: "INT-6", name: "PagerDuty", category: "Comms", description: "Escalate critical clusters to on-call.", status: "error", lastSync: "2h ago" },
];

export interface ApiKey {
  id: string;
  label: string;
  prefix: string;
  created: string;
  lastUsed: string;
}

export const apiKeys: ApiKey[] = [
  { id: "K-1", label: "Production · Backend", prefix: "fxl_live_8a3f", created: "2025-11-02", lastUsed: "2m ago" },
  { id: "K-2", label: "Staging · CI", prefix: "fxl_test_91dc", created: "2026-01-18", lastUsed: "12h ago" },
  { id: "K-3", label: "Data Warehouse Sync", prefix: "fxl_live_4b21", created: "2025-12-09", lastUsed: "3d ago" },
];

export const recentActivity = [
  { id: "AC-1", action: "Approved fix plan", target: "CL-1042 · Bulk CSV Export", time: "8m ago" },
  { id: "AC-2", action: "Commented on investigation", target: "AI-7728 · SSO Re-Auth Loop", time: "1h ago" },
  { id: "AC-3", action: "Exported executive report", target: "Q2 2026 Summary", time: "3h ago" },
  { id: "AC-4", action: "Invited team member", target: "devon.park@acmecorp.com", time: "Yesterday" },
  { id: "AC-5", action: "Marked cluster resolved", target: "CL-1028 · Webhook Retries", time: "2 days ago" },
];