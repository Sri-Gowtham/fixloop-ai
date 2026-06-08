import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { executiveSummary, revenueImpact, clusters } from "@/lib/mock-data";
import { Download, Printer, TrendingUp } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export const Route = createFileRoute("/_app/report")({
  head: () => ({ meta: [{ title: "Executive Report · FixLoop AI" }] }),
  component: ReportPage,
});

const axis = {
  stroke: "var(--muted-foreground)",
  fontSize: 10,
  tickLine: false,
  axisLine: false,
} as const;
const tip = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 12,
} as const;

function ReportPage() {
  const s = executiveSummary;
  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <PageHeader
        eyebrow={`${s.quarter} · Executive Brief`}
        title="Product Intelligence Report"
        description="Board-ready summary of customer pain points, financial impact, and shipped fixes."
        actions={
          <>
            <FxButton variant="outline" size="sm">
              <Printer className="h-3.5 w-3.5" />
              Print
            </FxButton>
            <FxButton size="sm">
              <Download className="h-3.5 w-3.5" />
              Export PDF
            </FxButton>
          </>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Tickets Analyzed" value={s.totalTickets.toLocaleString()} />
        <KpiCard label="Active Clusters" value={s.activeClusters.toString()} />
        <KpiCard
          label="Revenue at Risk"
          value={`$${(s.revenueAtRisk / 1000).toFixed(0)}k`}
          tone="critical"
        />
        <KpiCard
          label="Revenue Recovered"
          value={`$${(s.revenueRecovered / 1000).toFixed(0)}k`}
          tone="secondary"
        />
      </div>

      <Panel title="Quarterly Product Health" subtitle="Revenue at risk vs recovered, $ thousands">
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={revenueImpact}>
              <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="month" {...axis} />
              <YAxis {...axis} />
              <Tooltip contentStyle={tip} />
              <Line
                type="monotone"
                dataKey="atRisk"
                stroke="var(--critical)"
                strokeWidth={2.5}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="recovered"
                stroke="var(--secondary)"
                strokeWidth={2.5}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Top Issues This Quarter"
        subtitle="Ranked by combined severity, volume, and revenue impact"
      >
        <ol className="space-y-3">
          {s.topIssues.map((c, i) => (
            <li
              key={c.id}
              className="flex items-center gap-4 rounded-md border border-border bg-surface p-4"
            >
              <div className="text-2xl font-bold text-mono text-muted-foreground w-8">
                {String(i + 1).padStart(2, "0")}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold">{c.title}</div>
                <div className="text-xs text-muted-foreground text-mono">
                  {c.id} · {c.ticketCount} tickets · {c.affectedCustomers} customers
                </div>
              </div>
              <SeverityBadge severity={c.severity} />
              <div className="text-right">
                <div className="text-sm font-bold text-mono text-primary">
                  ${(c.monthlyCost / 1000).toFixed(1)}k
                </div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  monthly
                </div>
              </div>
            </li>
          ))}
        </ol>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Financial Impact Breakdown">
          <ul className="space-y-3">
            {clusters.slice(0, 6).map((c) => {
              const pct = (c.monthlyCost / s.revenueAtRisk) * 100;
              return (
                <li key={c.id}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-medium truncate pr-2">{c.title}</span>
                    <span className="text-mono text-primary">
                      ${(c.monthlyCost / 1000).toFixed(1)}k
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-surface overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${pct}%`, background: "var(--gradient-primary)" }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        </Panel>

        <Panel title="Priority Ranking & Recommended Actions">
          <ol className="space-y-3">
            {s.priorities.map((p) => (
              <li key={p.rank} className="rounded-md border border-border bg-surface p-3">
                <div className="flex items-center gap-2">
                  <span
                    className="h-6 w-6 rounded-full flex items-center justify-center text-[11px] font-bold text-mono"
                    style={{
                      background: "var(--gradient-cyber)",
                      color: "var(--primary-foreground)",
                    }}
                  >
                    {p.rank}
                  </span>
                  <span className="text-mono text-xs text-muted-foreground">{p.cluster}</span>
                </div>
                <div className="mt-1.5 text-sm text-muted-foreground">{p.reason}</div>
                <div className="mt-1.5 text-sm font-semibold text-primary flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5" />
                  {p.action}
                </div>
              </li>
            ))}
          </ol>
        </Panel>
      </div>

      <Panel title="Executive Summary">
        <div className="prose-sm text-sm text-muted-foreground space-y-3">
          <p>
            In {s.quarter}, FixLoop AI analyzed{" "}
            <span className="text-foreground font-semibold text-mono">
              {s.totalTickets.toLocaleString()}
            </span>{" "}
            support tickets and surfaced{" "}
            <span className="text-foreground font-semibold text-mono">{s.activeClusters}</span>{" "}
            active root-cause clusters representing{" "}
            <span className="text-primary font-semibold text-mono">
              ${(s.revenueAtRisk / 1000).toFixed(0)}k
            </span>{" "}
            in revenue at risk.
          </p>
          <p>
            Verified fixes shipped this quarter recovered{" "}
            <span className="text-secondary font-semibold text-mono">
              ${(s.revenueRecovered / 1000).toFixed(0)}k
            </span>{" "}
            with an aggregate deflection rate of{" "}
            <span className="text-secondary font-semibold text-mono">
              {Math.round(s.deflectionRate * 100)}%
            </span>
            . The remaining backlog is concentrated in authentication and reporting, with deploys
            v2.4.1 and v2.4.2 identified as causal events.
          </p>
          <p>
            Recommended next action: prioritize the Bulk CSV Export hotfix and roll back SameSite
            strict for IdP callback routes; together these account for{" "}
            <span className="text-foreground font-semibold text-mono">~62%</span> of remaining
            at-risk revenue.
          </p>
        </div>
      </Panel>
    </div>
  );
}

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "critical" | "secondary";
}) {
  const color =
    tone === "critical"
      ? "var(--critical)"
      : tone === "secondary"
        ? "var(--secondary)"
        : "var(--foreground)";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1.5 text-2xl font-bold text-mono" style={{ color }}>
        {value}
      </div>
    </div>
  );
}
