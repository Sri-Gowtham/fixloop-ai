import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { StatusBadge } from "@/components/fixloop/SeverityBadge";
import { resolutions } from "@/lib/mock-data";
import { CheckCircle2, ArrowRight, TrendingDown, DollarSign } from "lucide-react";

export const Route = createFileRoute("/_app/resolution")({
  head: () => ({ meta: [{ title: "Resolution Center · FixLoop AI" }] }),
  component: ResolutionPage,
});

function ResolutionPage() {
  const resolved = resolutions.filter((r) => r.status === "resolved");

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="Close the loop"
        title="Resolution Center"
        description="Track fixes from proposal to verified deflection. Every resolution closes the loop with measured ticket reduction and recovered revenue."
        actions={<FxButton size="sm">Open ticket review</FxButton>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <StatPill label="Open" value={resolutions.filter(r => r.status === "open").length} tone="critical" />
        <StatPill label="In Progress" value={resolutions.filter(r => r.status === "in_progress").length} tone="warning" />
        <StatPill label="Resolved (Q2)" value={resolved.length} tone="secondary" />
      </div>

      <Panel title="Loop Closures" subtitle="Verified before/after ticket volume per shipped fix">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resolved.map((r) => (
            <div key={r.id} className="rounded-lg border border-secondary/30 bg-secondary/5 p-5 relative overflow-hidden">
              <div className="absolute inset-x-0 top-0 h-px" style={{ background: "linear-gradient(90deg, transparent, var(--secondary), transparent)" }} />
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] text-mono text-muted-foreground uppercase tracking-wider">{r.clusterId}</div>
                  <h3 className="mt-1 text-base font-bold leading-tight">{r.issue}</h3>
                </div>
                <div className="h-9 w-9 rounded-full bg-secondary/20 flex items-center justify-center">
                  <CheckCircle2 className="h-5 w-5 text-secondary" />
                </div>
              </div>

              <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                <div className="rounded-md border border-border bg-card p-3 text-center">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Before fix</div>
                  <div className="mt-1 text-2xl font-bold text-mono text-[color:var(--critical)]">{r.before}</div>
                  <div className="text-[10px] text-muted-foreground">tickets / mo</div>
                </div>
                <ArrowRight className="h-5 w-5 text-secondary" />
                <div className="rounded-md border border-secondary/40 bg-secondary/10 p-3 text-center">
                  <div className="text-[10px] uppercase tracking-wider text-secondary">After fix</div>
                  <div className="mt-1 text-2xl font-bold text-mono text-secondary">{r.after}</div>
                  <div className="text-[10px] text-muted-foreground">tickets / mo</div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2"><TrendingDown className="h-4 w-4 text-secondary" /><span className="font-semibold text-mono">{r.expectedReduction}%</span> deflection</div>
                <div className="flex items-center gap-2"><DollarSign className="h-4 w-4 text-primary" /><span className="font-semibold text-mono text-primary">${(r.costRecovery/1000).toFixed(1)}k</span> / mo</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="All Resolutions" subtitle="Pipeline from detection to verified fix">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
                <th className="text-left font-semibold py-2">Issue</th>
                <th className="text-left font-semibold py-2">Recommended fix</th>
                <th className="text-left font-semibold py-2">Owner</th>
                <th className="text-right font-semibold py-2">Reduction</th>
                <th className="text-right font-semibold py-2">Recovery</th>
                <th className="text-right font-semibold py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {resolutions.map((r) => (
                <tr key={r.id} className="border-b border-border/50 align-top hover:bg-accent/30">
                  <td className="py-3 pr-3">
                    <div className="font-medium">{r.issue}</div>
                    <div className="text-xs text-muted-foreground text-mono">{r.clusterId}</div>
                  </td>
                  <td className="py-3 pr-3 text-muted-foreground max-w-md">{r.fix}</td>
                  <td className="py-3 pr-3 text-mono text-xs">{r.owner}</td>
                  <td className="py-3 text-right text-mono text-secondary font-semibold">{r.expectedReduction}%</td>
                  <td className="py-3 text-right text-mono text-primary font-semibold">${(r.costRecovery/1000).toFixed(1)}k</td>
                  <td className="py-3 text-right"><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function StatPill({ label, value, tone }: { label: string; value: number; tone: "critical" | "warning" | "secondary" }) {
  const color = { critical: "var(--critical)", warning: "var(--warning)", secondary: "var(--secondary)" }[tone];
  return (
    <div className="rounded-lg border border-border bg-card p-5 relative overflow-hidden">
      <div className="absolute inset-y-0 left-0 w-1" style={{ background: color }} />
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-3xl font-bold text-mono" style={{ color }}>{value}</div>
    </div>
  );
}