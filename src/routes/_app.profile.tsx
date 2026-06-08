import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { currentUser, recentActivity, integrations } from "@/lib/mock-data";
import {
  Mail,
  Building2,
  Shield,
  Globe2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Bell,
  Edit3,
} from "lucide-react";

export const Route = createFileRoute("/_app/profile")({
  head: () => ({ meta: [{ title: "Profile · FixLoop AI" }] }),
  component: ProfilePage,
});

function ProfilePage() {
  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Your identity, organization, notification preferences, and connected systems."
        actions={
          <FxButton size="sm" variant="outline">
            <Edit3 className="h-3.5 w-3.5" />
            Edit profile
          </FxButton>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Panel className="xl:col-span-1" title="User information">
          <div className="flex items-center gap-4">
            <div
              className="h-16 w-16 rounded-lg flex items-center justify-center text-xl font-bold text-primary-foreground text-mono"
              style={{ background: "var(--gradient-cyber)" }}
            >
              {currentUser.initials}
            </div>
            <div className="min-w-0">
              <div className="text-lg font-bold leading-tight">{currentUser.name}</div>
              <div className="text-xs text-muted-foreground">{currentUser.role}</div>
              <div className="mt-1 inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase tracking-wider">
                {currentUser.plan}
              </div>
            </div>
          </div>
          <div className="mt-5 space-y-2.5 text-sm">
            <InfoRow
              icon={<Mail className="h-3.5 w-3.5" />}
              label="Email"
              value={currentUser.email}
            />
            <InfoRow
              icon={<Building2 className="h-3.5 w-3.5" />}
              label="Company"
              value={currentUser.company}
            />
            <InfoRow
              icon={<Shield className="h-3.5 w-3.5" />}
              label="Role"
              value={currentUser.role}
            />
            <InfoRow
              icon={<Globe2 className="h-3.5 w-3.5" />}
              label="Timezone"
              value={currentUser.timezone}
            />
          </div>
        </Panel>

        <Panel
          className="xl:col-span-2"
          title="Notification preferences"
          subtitle="Control how the agent reaches you"
        >
          <div className="space-y-2">
            <NotifRow
              label="Critical clusters"
              description="When a new cluster crosses 400 tickets or $20k revenue risk."
              defaults={{ email: true, slack: true, inApp: true }}
            />
            <NotifRow
              label="New deploy correlations"
              description="When the agent links a deploy to a cluster with >85% confidence."
              defaults={{ email: false, slack: true, inApp: true }}
            />
            <NotifRow
              label="Fix validation results"
              description="When a deployed fix is verified by post-deploy ticket data."
              defaults={{ email: true, slack: true, inApp: true }}
            />
            <NotifRow
              label="Weekly executive digest"
              description="Sunday 6pm digest of revenue at risk, recovered, and top priorities."
              defaults={{ email: true, slack: false, inApp: false }}
            />
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Panel
          title="Recent activity"
          subtitle="Last 30 days"
          action={<Bell className="h-3.5 w-3.5 text-muted-foreground" />}
        >
          <ul className="space-y-1">
            {recentActivity.map((a) => (
              <li
                key={a.id}
                className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2.5"
              >
                <div className="h-7 w-7 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center text-primary text-[10px] font-bold text-mono">
                  {a.id.split("-")[1]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{a.action}</div>
                  <div className="text-xs text-muted-foreground truncate">{a.target}</div>
                </div>
                <div className="text-[10px] text-mono text-muted-foreground">{a.time}</div>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          title="Connected integrations"
          subtitle="Auth and data sources linked to your account"
        >
          <ul className="space-y-1">
            {integrations.slice(0, 6).map((i) => (
              <li
                key={i.id}
                className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2.5"
              >
                <div className="h-8 w-8 rounded-md border border-border bg-background flex items-center justify-center text-xs font-bold text-mono">
                  {i.name.slice(0, 2).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate">{i.name}</div>
                  <div className="text-xs text-muted-foreground truncate">{i.description}</div>
                </div>
                <StatusPill status={i.status} />
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border bg-surface px-3 py-2">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
        <span className="text-primary">{icon}</span>
        {label}
      </div>
      <div className="text-sm text-mono">{value}</div>
    </div>
  );
}

function NotifRow({
  label,
  description,
  defaults,
}: {
  label: string;
  description: string;
  defaults: { email: boolean; slack: boolean; inApp: boolean };
}) {
  return (
    <div className="flex items-center gap-4 rounded-md border border-border bg-surface px-3 py-3">
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold">{label}</div>
        <div className="text-xs text-muted-foreground">{description}</div>
      </div>
      <div className="flex items-center gap-1">
        <Toggle label="Email" on={defaults.email} />
        <Toggle label="Slack" on={defaults.slack} />
        <Toggle label="In-app" on={defaults.inApp} />
      </div>
    </div>
  );
}

function Toggle({ label, on }: { label: string; on: boolean }) {
  return (
    <div
      className={`h-7 px-2.5 rounded-md text-[10px] uppercase tracking-wider font-semibold border ${on ? "border-primary/40 bg-primary/10 text-primary" : "border-border bg-background text-muted-foreground"} flex items-center gap-1.5 text-mono`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${on ? "bg-primary" : "bg-muted-foreground/40"}`}
        style={on ? { boxShadow: "0 0 6px var(--primary)" } : undefined}
      />
      {label}
    </div>
  );
}

function StatusPill({ status }: { status: "connected" | "disconnected" | "error" }) {
  if (status === "connected")
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-secondary">
        <CheckCircle2 className="h-3 w-3" />
        Connected
      </span>
    );
  if (status === "error")
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-warning">
        <AlertTriangle className="h-3 w-3" />
        Error
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
      <XCircle className="h-3 w-3" />
      Disconnected
    </span>
  );
}
