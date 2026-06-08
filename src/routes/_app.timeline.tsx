import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { clusters, deploys } from "@/lib/mock-data";
import { GitBranch, Zap, AlertOctagon, Crosshair } from "lucide-react";

export const Route = createFileRoute("/_app/timeline")({
  head: () => ({ meta: [{ title: "Causal Timeline · FixLoop AI" }] }),
  component: TimelinePage,
});

function TimelinePage() {
  // Map events on a normalized horizontal axis (Apr 1 → Jun 8)
  const start = new Date("2026-04-01").getTime();
  const end = new Date("2026-06-08").getTime();
  const pos = (iso: string) => ((new Date(iso).getTime() - start) / (end - start)) * 100;

  type Pt = { id: string; x: number; y: number; kind: "deploy" | "cluster"; data: any };
  const deployPts: Pt[] = deploys.map((d, i) => ({
    id: d.id,
    x: pos(d.date),
    y: 18 + (i % 2) * 8,
    kind: "deploy",
    data: d,
  }));
  const clusterPts: Pt[] = clusters
    .slice(0, 8)
    .map((c, i) => ({
      id: c.id,
      x: pos(c.firstSeen),
      y: 65 + (i % 3) * 7,
      kind: "cluster",
      data: c,
    }));

  const links = clusters
    .filter((c) => c.relatedDeploy)
    .map((c) => {
      const d = deploys.find((x) => x.version === c.relatedDeploy);
      if (!d) return null;
      const from = deployPts.find((p) => p.id === d.id)!;
      const to = clusterPts.find((p) => p.id === c.id);
      if (!to) return null;
      return { from, to, confidence: c.confidence, severity: c.severity };
    })
    .filter(Boolean) as { from: Pt; to: Pt; confidence: number; severity: any }[];

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="Investigation"
        title="Causal Timeline"
        description="Overlay deploys, release notes, and discovered clusters. Correlation lines connect deploys to the issues they likely caused."
        actions={
          <>
            <FxButton variant="outline" size="sm">
              Apr — Jun 2026
            </FxButton>
            <FxButton size="sm">
              <Crosshair className="h-3.5 w-3.5" />
              Auto-correlate
            </FxButton>
          </>
        }
      />

      <Panel
        title="Deploy ↔ Cluster Correlation"
        subtitle="Lines show confidence-weighted causal links"
      >
        <div className="relative h-[460px] grid-bg rounded-md border border-border bg-surface overflow-hidden">
          {/* Center axis */}
          <div className="absolute left-0 right-0 top-1/2 h-px bg-border" />
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] uppercase tracking-wider text-muted-foreground bg-surface px-1.5 rotate-0">
            Timeline
          </div>

          {/* Date ticks */}
          {["Apr", "May", "Jun"].map((m, i) => (
            <div
              key={m}
              className="absolute top-0 bottom-0 border-l border-dashed border-border/60"
              style={{ left: `${(i / 2) * 100}%` }}
            >
              <span className="absolute -top-px left-1 text-[10px] uppercase text-mono text-muted-foreground">
                {m} 2026
              </span>
            </div>
          ))}

          {/* Correlation SVG layer */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {links.map((l, i) => {
              const x1 = `${l.from.x}%`,
                y1 = `${l.from.y}%`;
              const x2 = `${l.to.x}%`,
                y2 = `${l.to.y}%`;
              const color =
                l.severity === "critical"
                  ? "var(--critical)"
                  : l.severity === "high"
                    ? "var(--primary)"
                    : "var(--warning)";
              return (
                <g key={i}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={color}
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    opacity={l.confidence / 100}
                  />
                </g>
              );
            })}
          </svg>

          {/* Deploys (top half) */}
          {deployPts.map((p) => (
            <div
              key={p.id}
              className="absolute -translate-x-1/2 -translate-y-1/2 group"
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
            >
              <div className="flex flex-col items-center gap-1">
                <div className="h-7 w-7 rounded-md border border-secondary/40 bg-secondary/10 flex items-center justify-center">
                  <GitBranch className="h-3.5 w-3.5 text-secondary" />
                </div>
                <div className="text-[10px] text-mono text-secondary font-semibold whitespace-nowrap">
                  {p.data.version}
                </div>
              </div>
              <div className="absolute left-1/2 -translate-x-1/2 mt-1.5 hidden group-hover:block z-30 w-56 rounded-md border border-border bg-card p-3 shadow-lg">
                <div className="text-xs font-semibold">{p.data.title}</div>
                <div className="mt-1 text-[10px] text-muted-foreground text-mono">
                  {p.data.date} · {p.data.version}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">{p.data.notes}</div>
              </div>
            </div>
          ))}

          {/* Clusters (bottom half) */}
          {clusterPts.map((p) => {
            const color =
              p.data.severity === "critical"
                ? "var(--critical)"
                : p.data.severity === "high"
                  ? "var(--primary)"
                  : p.data.severity === "medium"
                    ? "var(--warning)"
                    : "var(--secondary)";
            return (
              <div
                key={p.id}
                className="absolute -translate-x-1/2 -translate-y-1/2 group"
                style={{ left: `${p.x}%`, top: `${p.y}%` }}
              >
                <div className="flex flex-col items-center gap-1">
                  <div className="text-[10px] text-mono whitespace-nowrap" style={{ color }}>
                    {p.data.id}
                  </div>
                  <div
                    className="h-8 w-8 rounded-full border-2 flex items-center justify-center"
                    style={{
                      borderColor: color,
                      background: `color-mix(in oklab, ${color} 15%, transparent)`,
                    }}
                  >
                    <AlertOctagon className="h-4 w-4" style={{ color }} />
                  </div>
                </div>
                <div className="absolute left-1/2 -translate-x-1/2 mt-1.5 hidden group-hover:block z-30 w-64 rounded-md border border-border bg-card p-3 shadow-lg">
                  <div className="text-xs font-semibold">{p.data.title}</div>
                  <div className="mt-1 text-[10px] text-muted-foreground text-mono">
                    {p.data.ticketCount} tickets · {p.data.confidence}% confidence
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4 text-xs">
          <Legend color="var(--secondary)" label="Deploy event" />
          <Legend color="var(--critical)" label="Critical cluster" />
          <Legend color="var(--primary)" label="High severity" />
          <Legend color="var(--warning)" label="Medium severity" />
          <span className="ml-auto inline-flex items-center gap-2 text-muted-foreground">
            <span
              className="h-px w-6"
              style={{ borderTop: "1.5px dashed var(--muted-foreground)" }}
            />
            Correlation
          </span>
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Correlated Findings" subtitle="Causal links FixLoop AI surfaced this quarter">
          <ul className="space-y-3">
            {clusters
              .filter((c) => c.relatedDeploy)
              .slice(0, 5)
              .map((c) => (
                <li key={c.id} className="rounded-md border border-border bg-surface p-4">
                  <div className="flex items-center gap-2 text-xs text-mono text-muted-foreground">
                    <Zap className="h-3 w-3 text-primary" />
                    Deploy {c.relatedDeploy}
                    <span>→</span>
                    <span>3-7 days later</span>
                    <span>→</span>
                    <span className="text-primary">{c.id}</span>
                  </div>
                  <div className="mt-1.5 text-sm font-semibold">{c.title}</div>
                  <div className="mt-1.5 flex items-center gap-3 text-xs">
                    <SeverityBadge severity={c.severity} />
                    <span className="text-secondary font-semibold text-mono">
                      {c.confidence}% confidence
                    </span>
                    <span className="text-muted-foreground text-mono ml-auto">
                      {c.ticketCount} tickets
                    </span>
                  </div>
                </li>
              ))}
          </ul>
        </Panel>

        <Panel title="Release Notes" subtitle="Annotated with downstream impact">
          <ul className="space-y-3">
            {deploys.map((d) => (
              <li key={d.id} className="rounded-md border border-border bg-surface p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-3.5 w-3.5 text-secondary" />
                    <span className="text-sm font-semibold text-mono">{d.version}</span>
                    <span className="text-xs text-muted-foreground">{d.date}</span>
                  </div>
                  <SeverityBadge severity={d.risk} />
                </div>
                <div className="mt-1.5 text-sm">{d.title}</div>
                <div className="text-xs text-muted-foreground">{d.notes}</div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-muted-foreground">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
