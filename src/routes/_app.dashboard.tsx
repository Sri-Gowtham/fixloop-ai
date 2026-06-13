import { createFileRoute } from "@tanstack/react-router";
import { MetricCard } from "@/components/fixloop/MetricCard";
import { Panel } from "@/components/fixloop/Panel";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { FxButton } from "@/components/fixloop/Button";
import {
  clusters,
  ticketVolumeTrend,
  revenueImpact,
  clusterDistribution,
  recentAlerts,
  productHealthScore,
  rootCauseHeatmap,
} from "@/lib/mock-data";
import {
  Activity,
  AlertOctagon,
  DollarSign,
  Users,
  ShieldCheck,
  Download,
  Filter,
  Lightbulb,
  CheckCircle,
  Server,
  Ticket,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import { useClusters } from "@/hooks/useClusters";
import { useStats } from "@/hooks/useStats";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · FixLoop AI" }] }),
  component: DashboardPage,
});

const axisProps = {
  stroke: "var(--muted-foreground)",
  fontSize: 10,
  tickLine: false,
  axisLine: false,
} as const;
const tooltipStyle = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 12,
  color: "var(--foreground)",
} as const;

function DashboardPage() {
  // Fetch live clusters for the top table
  const { data: liveClusters = [], isLoading: isLoadingClusters } = useClusters(1, 6);
  // Fetch live stats
  const { data: stats, isLoading: isLoadingStats } = useStats();

  return (
    <div className="p-8 space-y-8">
      <PageHeader
        eyebrow="Operations · Live"
        title="Product Intelligence Dashboard"
        description="Real-time view of where customer pain is concentrated, what it's costing, and which fixes are working."
        actions={
          <>
            <FxButton variant="outline" size="sm">
              <Filter className="h-3.5 w-3.5" />
              Last 30 days
            </FxButton>
            <FxButton size="sm">
              <Download className="h-3.5 w-3.5" />
              Export
            </FxButton>
          </>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <PremiumMetricCard
          label="Total Tickets"
          value={isLoadingStats ? "-" : (stats?.total_tickets ?? 0).toLocaleString()}
          icon={Ticket}
          accent="text-blue-500"
          bg="bg-blue-500/10"
          border="border-blue-500/20"
        />
        <PremiumMetricCard
          label="Active Clusters"
          value={isLoadingStats ? "-" : stats?.active_clusters?.toString()}
          icon={AlertOctagon}
          accent="text-[color:var(--primary)]"
          bg="bg-primary/10"
          border="border-primary/20"
        />
        <PremiumMetricCard
          label="Revenue Risk"
          value={isLoadingStats ? "-" : `$${((stats?.revenue_risk_usd ?? 0) / 1000).toFixed(1)}k`}
          icon={DollarSign}
          accent="text-[color:var(--critical)]"
          bg="bg-critical/10"
          border="border-critical/20"
        />
        <PremiumMetricCard
          label="Recommendations"
          value={isLoadingStats ? "-" : stats?.recommendations_generated?.toString()}
          icon={Lightbulb}
          accent="text-[color:var(--warning)]"
          bg="bg-warning/10"
          border="border-warning/20"
        />
        <PremiumMetricCard
          label="Fix Success Rate"
          value={isLoadingStats ? "-" : `${stats?.fix_success_rate_pct ?? 0}%`}
          icon={CheckCircle}
          accent="text-[color:var(--secondary)]"
          bg="bg-secondary/10"
          border="border-secondary/20"
        />
        <PremiumMetricCard
          label="Deployments Tracked"
          value={isLoadingStats ? "-" : stats?.deployments_tracked?.toString()}
          icon={Server}
          accent="text-purple-500"
          bg="bg-purple-500/10"
          border="border-purple-500/20"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Panel
          title="Product Health Score"
          subtitle="Composite of severity, deflection rate, and deploy stability"
          className="xl:col-span-1"
        >
          <HealthGauge value={productHealthScore} />
        </Panel>
        <Panel
          title="Ticket Volume vs Resolution"
          subtitle="7-day rolling"
          className="xl:col-span-2"
          action={<Legend2 />}
        >
          <div className="h-64">
            <ResponsiveContainer>
              <AreaChart data={ticketVolumeTrend}>
                <defs>
                  <linearGradient id="g-tickets" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="g-resolved" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="var(--secondary)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="var(--secondary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="day" {...axisProps} />
                <YAxis {...axisProps} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ stroke: "var(--primary)", strokeOpacity: 0.3 }}
                />
                <Area
                  type="monotone"
                  dataKey="tickets"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  fill="url(#g-tickets)"
                />
                <Area
                  type="monotone"
                  dataKey="resolved"
                  stroke="var(--secondary)"
                  strokeWidth={2}
                  fill="url(#g-resolved)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Panel title="Cluster Distribution" subtitle="By product area">
          <div className="h-56">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={clusterDistribution}
                  dataKey="value"
                  innerRadius={48}
                  outerRadius={80}
                  stroke="var(--background)"
                  strokeWidth={2}
                >
                  {clusterDistribution.map((d, i) => (
                    <Cell key={i} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5">
            {clusterDistribution.map((d) => (
              <li key={d.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="h-2 w-2 rounded-sm" style={{ background: d.color }} />
                  {d.name}
                </span>
                <span className="text-mono">{d.value}%</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          title="Revenue Impact"
          subtitle="At-risk vs recovered ($ thousands)"
          className="xl:col-span-2"
        >
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={revenueImpact}>
                <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="month" {...axisProps} />
                <YAxis {...axisProps} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: "var(--accent)", opacity: 0.3 }}
                />
                <Bar dataKey="atRisk" fill="var(--critical)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="recovered" fill="var(--secondary)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Panel title="Recent Alerts" subtitle="Last 24 hours" className="xl:col-span-1">
          <ul className="divide-y divide-border -mx-5">
            {recentAlerts.map((a) => (
              <li key={a.id} className="px-5 py-3 flex items-start gap-3">
                <SeverityBadge severity={a.severity} />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">{a.title}</div>
                  <div className="text-xs text-muted-foreground truncate">{a.detail}</div>
                </div>
                <span className="text-[10px] text-mono text-muted-foreground whitespace-nowrap">
                  {a.time}
                </span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          title="Root Cause Heatmap"
          subtitle="Ticket density by product area × day"
          className="xl:col-span-2"
        >
          <Heatmap />
        </Panel>
      </div>

      <Panel
        title="Top Clusters"
        subtitle="Sorted by revenue impact"
        action={
          <FxButton variant="ghost" size="sm">
            View all
          </FxButton>
        }
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
              <th className="text-left font-semibold py-2">Cluster</th>
              <th className="text-left font-semibold py-2">Severity</th>
              <th className="text-right font-semibold py-2">Tickets</th>
              <th className="text-right font-semibold py-2">Customers</th>
              <th className="text-right font-semibold py-2">Cost / mo</th>
              <th className="text-right font-semibold py-2">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {isLoadingClusters ? (
              <tr>
                <td colSpan={6} className="py-4 text-center text-muted-foreground">
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    Loading clusters...
                  </div>
                </td>
              </tr>
            ) : liveClusters.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-4 text-center text-muted-foreground">
                  No clusters found.
                </td>
              </tr>
            ) : (
              liveClusters.map((c) => (
                <tr key={c.id} className="border-b border-border/50 hover:bg-accent/30">
                  <td className="py-3">
                    <div className="font-medium">{c.title}</div>
                    <div className="text-xs text-muted-foreground text-mono">
                      {c.id.split("-")[0]}-{c.id.slice(-4)}
                      {c.related_deploy_id ? ` · ${c.related_deploy_id}` : ""}
                    </div>
                  </td>
                  <td>
                    <SeverityBadge severity={c.severity as any} />
                  </td>
                  <td className="text-right text-mono">{c.ticket_count}</td>
                  <td className="text-right text-mono">{c.affected_customers}</td>
                  <td className="text-right text-mono text-primary">
                    ${(c.monthly_cost_usd / 1000).toFixed(1)}k
                  </td>
                  <td className="text-right text-mono">
                    {c.confidence ? `${c.confidence.toFixed(1)}%` : "-"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}

function Legend2() {
  return (
    <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-sm bg-primary" />
        Tickets
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-sm bg-secondary" />
        Resolved
      </span>
    </div>
  );
}

function HealthGauge({ value }: { value: number }) {
  const r = 70;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c * 0.75; // 3/4 arc
  const arcLen = c * 0.75;
  return (
    <div className="flex flex-col items-center">
      <div className="relative h-44 w-44">
        <svg viewBox="0 0 200 200" className="-rotate-[135deg]">
          <circle
            cx="100"
            cy="100"
            r={r}
            stroke="var(--border)"
            strokeWidth="14"
            fill="none"
            strokeDasharray={`${arcLen} ${c}`}
            strokeLinecap="round"
          />
          <circle
            cx="100"
            cy="100"
            r={r}
            stroke="url(#gauge)"
            strokeWidth="14"
            fill="none"
            strokeDasharray={`${arcLen - offset} ${c}`}
            strokeLinecap="round"
          />
          <defs>
            <linearGradient id="gauge" x1="0" x2="1">
              <stop offset="0%" stopColor="var(--critical)" />
              <stop offset="50%" stopColor="var(--warning)" />
              <stop offset="100%" stopColor="var(--secondary)" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold text-mono">{value}</div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">/ 100</div>
        </div>
      </div>
      <div className="mt-2 text-xs text-center">
        <div className="text-secondary font-semibold">Stable</div>
        <div className="text-muted-foreground">+6 pts vs last week</div>
      </div>
    </div>
  );
}

function Heatmap() {
  const max = Math.max(...rootCauseHeatmap.flatMap((r) => r.values));
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return (
    <div>
      <div className="grid grid-cols-[80px_repeat(7,1fr)] gap-1 text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
        <div />
        {days.map((d) => (
          <div key={d} className="text-center">
            {d}
          </div>
        ))}
      </div>
      <div className="space-y-1">
        {rootCauseHeatmap.map((row) => (
          <div key={row.area} className="grid grid-cols-[80px_repeat(7,1fr)] gap-1 items-center">
            <div className="text-xs font-medium text-muted-foreground">{row.area}</div>
            {row.values.map((v, i) => {
              const intensity = v / max;
              return (
                <div
                  key={i}
                  className="h-8 rounded-sm border border-border/40 flex items-center justify-center text-[10px] text-mono"
                  style={{
                    background: `color-mix(in oklab, var(--primary) ${Math.round(intensity * 80)}%, var(--card))`,
                    color:
                      intensity > 0.5 ? "var(--primary-foreground)" : "var(--muted-foreground)",
                  }}
                >
                  {v}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function PremiumMetricCard({
  label,
  value,
  icon: Icon,
  accent,
  bg,
  border,
}: {
  label: string;
  value: string | undefined;
  icon: any;
  accent: string;
  bg: string;
  border: string;
}) {
  return (
    <div
      className={`group relative overflow-hidden rounded-xl border ${border} bg-card/40 p-6 backdrop-blur-xl shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:bg-card/60`}
    >
      <div
        className={`absolute -right-12 -top-12 h-32 w-32 rounded-full ${bg} blur-2xl transition-all duration-500 group-hover:scale-150`}
      />
      <div className="relative flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-muted-foreground font-medium mb-1">
            {label}
          </div>
          <div className="text-3xl font-bold tracking-tight text-foreground mt-1">
            {value}
          </div>
        </div>
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${bg} ${border} border`}>
          <Icon className={`h-6 w-6 ${accent}`} />
        </div>
      </div>
    </div>
  );
}
