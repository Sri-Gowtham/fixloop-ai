import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { integrations, teamMembers, apiKeys, currentUser } from "@/lib/mock-data";
import {
  Plug,
  Users,
  Building2,
  KeyRound,
  Bell,
  Plus,
  Copy,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Trash2,
  Mail,
} from "lucide-react";

export const Route = createFileRoute("/_app/settings")({
  head: () => ({ meta: [{ title: "Settings · FixLoop AI" }] }),
  component: SettingsPage,
});

const TABS = [
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "team", label: "Team", icon: Users },
  { id: "org", label: "Organization", icon: Building2 },
  { id: "api", label: "API Keys", icon: KeyRound },
  { id: "notifications", label: "Notifications", icon: Bell },
] as const;

function SettingsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("integrations");

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Configure data sources, manage your team, and tune how FixLoop AI plugs into your stack."
        actions={
          <FxButton size="sm" variant="cyber">
            Save configuration
          </FxButton>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3">
          <div className="rounded-lg border border-border bg-card p-2 space-y-0.5">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium ${tab === t.id ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-accent/50"}`}
              >
                <t.icon className={`h-4 w-4 ${tab === t.id ? "text-primary" : ""}`} />
                {t.label}
              </button>
            ))}
          </div>
        </aside>

        <div className="lg:col-span-9 space-y-4">
          {tab === "integrations" && <IntegrationsTab />}
          {tab === "team" && <TeamTab />}
          {tab === "org" && <OrgTab />}
          {tab === "api" && <ApiTab />}
          {tab === "notifications" && <NotificationsTab />}
        </div>
      </div>
    </div>
  );
}

function IntegrationsTab() {
  return (
    <Panel
      title="Integrations"
      subtitle="Connect ticketing, source, and comms tools"
      action={
        <FxButton size="sm" variant="outline">
          <Plus className="h-3.5 w-3.5" />
          Browse marketplace
        </FxButton>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {integrations.map((i) => (
          <div key={i.id} className="rounded-md border border-border bg-surface p-4">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-md border border-border bg-background flex items-center justify-center text-sm font-bold text-mono">
                {i.name.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <div className="text-sm font-bold">{i.name}</div>
                  <span className="text-[9px] uppercase tracking-wider text-muted-foreground border border-border rounded px-1.5 py-0.5">
                    {i.category}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">{i.description}</div>
                <div className="mt-3 flex items-center gap-2 text-[10px] text-mono text-muted-foreground">
                  {i.status === "connected" && (
                    <span className="inline-flex items-center gap-1 text-secondary">
                      <CheckCircle2 className="h-3 w-3" />
                      Connected · {i.lastSync}
                      {i.records ? ` · ${i.records.toLocaleString()} records` : ""}
                    </span>
                  )}
                  {i.status === "error" && (
                    <span className="inline-flex items-center gap-1 text-warning">
                      <AlertTriangle className="h-3 w-3" />
                      Reauth required
                    </span>
                  )}
                  {i.status === "disconnected" && (
                    <span className="inline-flex items-center gap-1">
                      <XCircle className="h-3 w-3" />
                      Not connected
                    </span>
                  )}
                </div>
              </div>
              <FxButton size="sm" variant={i.status === "connected" ? "outline" : "cyber"}>
                {i.status === "connected"
                  ? "Configure"
                  : i.status === "error"
                    ? "Reconnect"
                    : "Connect"}
              </FxButton>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function TeamTab() {
  return (
    <Panel
      title="Team management"
      subtitle={`${teamMembers.filter((m) => m.status === "active").length} active · ${teamMembers.filter((m) => m.status === "invited").length} pending`}
      action={
        <FxButton size="sm" variant="cyber">
          <Mail className="h-3.5 w-3.5" />
          Invite member
        </FxButton>
      }
    >
      <div className="rounded-md border border-border bg-surface overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-background/40 text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="text-left px-4 py-2 font-semibold">Member</th>
              <th className="text-left px-4 py-2 font-semibold">Role</th>
              <th className="text-left px-4 py-2 font-semibold">Status</th>
              <th className="text-left px-4 py-2 font-semibold">Last active</th>
              <th className="text-right px-4 py-2 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {teamMembers.map((m) => (
              <tr key={m.id} className="border-t border-border">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className="h-7 w-7 rounded-md flex items-center justify-center text-[10px] font-bold text-primary-foreground text-mono"
                      style={{ background: "var(--gradient-cyber)" }}
                    >
                      {m.name
                        .split(" ")
                        .map((s) => s[0])
                        .slice(0, 2)
                        .join("")
                        .toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium truncate">{m.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{m.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center text-[10px] font-semibold uppercase tracking-wider rounded-md px-2 py-0.5 ${m.role === "Owner" ? "bg-primary/15 text-primary border border-primary/30" : "border border-border text-muted-foreground"}`}
                  >
                    {m.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {m.status === "active" ? (
                    <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-secondary">
                      <span className="h-1.5 w-1.5 rounded-full bg-secondary" />
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-warning">
                      <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                      Invited
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-mono text-xs text-muted-foreground">
                  {m.lastActive}
                </td>
                <td className="px-4 py-3 text-right">
                  <button className="text-xs text-muted-foreground hover:text-foreground">
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function OrgTab() {
  return (
    <div className="space-y-4">
      <Panel title="Organization">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Field label="Workspace name" value={currentUser.company} />
          <Field label="Workspace slug" value="acme-corp" mono />
          <Field label="Primary domain" value="acmecorp.com" mono />
          <Field label="Plan" value={`${currentUser.plan} · 25 seats`} />
          <Field label="Data region" value="US-East · Virginia" />
          <Field label="Default timezone" value={currentUser.timezone} mono />
        </div>
      </Panel>
      <Panel title="Danger zone">
        <div className="flex items-center justify-between rounded-md border border-critical/30 bg-critical/5 p-3">
          <div>
            <div className="text-sm font-bold">Delete workspace</div>
            <div className="text-xs text-muted-foreground">
              Permanently remove all clusters, integrations, and audit history.
            </div>
          </div>
          <FxButton
            size="sm"
            variant="outline"
            className="border-critical/40 text-critical hover:text-critical"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </FxButton>
        </div>
      </Panel>
    </div>
  );
}

function ApiTab() {
  return (
    <Panel
      title="API keys"
      subtitle="Server-to-server credentials"
      action={
        <FxButton size="sm" variant="cyber">
          <Plus className="h-3.5 w-3.5" />
          Generate key
        </FxButton>
      }
    >
      <div className="rounded-md border border-border bg-surface overflow-hidden">
        {apiKeys.map((k, idx) => (
          <div
            key={k.id}
            className={`flex items-center gap-3 px-4 py-3 ${idx > 0 ? "border-t border-border" : ""}`}
          >
            <div className="h-8 w-8 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
              <KeyRound className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold truncate">{k.label}</div>
              <div className="text-xs text-mono text-muted-foreground">
                {k.prefix}••••••••••••••••
              </div>
            </div>
            <div className="text-xs text-mono text-muted-foreground hidden md:block">
              Last used {k.lastUsed}
            </div>
            <button className="h-8 w-8 rounded-md border border-border bg-background hover:border-primary/40 flex items-center justify-center text-muted-foreground hover:text-foreground">
              <Copy className="h-3.5 w-3.5" />
            </button>
            <button className="h-8 w-8 rounded-md border border-border bg-background hover:border-primary/40 flex items-center justify-center text-muted-foreground hover:text-foreground">
              <RotateCw className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function NotificationsTab() {
  return (
    <Panel title="Notification routing" subtitle="Workspace-wide defaults">
      <div className="space-y-2">
        {[
          {
            label: "Critical cluster detected",
            chans: ["Email", "Slack #fixloop-alerts", "PagerDuty"],
          },
          { label: "Deploy correlation > 85%", chans: ["Slack #engineering", "In-app"] },
          { label: "Fix verified (loop closed)", chans: ["Email", "Slack #product"] },
          { label: "Weekly executive digest", chans: ["Email — leads@acmecorp.com"] },
        ].map((r) => (
          <div
            key={r.label}
            className="rounded-md border border-border bg-surface px-3 py-3 flex items-center gap-3"
          >
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold">{r.label}</div>
              <div className="text-xs text-muted-foreground truncate">{r.chans.join(" · ")}</div>
            </div>
            <FxButton size="sm" variant="outline">
              Edit
            </FxButton>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">{label}</div>
      <div
        className={`h-10 rounded-md border border-border bg-surface px-3 flex items-center text-sm ${mono ? "text-mono" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}
