import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { ClusterCard } from "@/components/fixloop/ClusterCard";
import { Panel } from "@/components/fixloop/Panel";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { FxButton } from "@/components/fixloop/Button";
import { type Severity } from "@/lib/mock-data";
import { Search, SlidersHorizontal, X, Loader2 } from "lucide-react";
import { useClusters, type ClusterOut } from "@/hooks/useClusters";

export const Route = createFileRoute("/_app/clusters")({
  head: () => ({ meta: [{ title: "Clusters · FixLoop AI" }] }),
  component: ClustersPage,
});

const SEVS: (Severity | "all")[] = ["all", "critical", "high", "medium", "low"];

function ClustersPage() {
  const [q, setQ] = useState("");
  const [sev, setSev] = useState<Severity | "all">("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const {
    data: liveClusters = [],
    isLoading: isLoadingClusters,
    isError: isClustersError,
  } = useClusters(
    1,
    50,
    sev !== "all" ? sev : undefined,
  );

  const filtered = liveClusters.filter((c) => c.title.toLowerCase().includes(q.toLowerCase()));

  const selected = liveClusters.find((c) => c.id === selectedId) || liveClusters[0];

  if (isClustersError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-lg font-bold text-critical">Cannot load clusters</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          The AI service at <code className="text-mono text-primary">{import.meta.env.VITE_API_URL || "http://localhost:8000"}</code> is not responding.
          Start the FastAPI backend (<code className="text-mono">uvicorn main:app --reload --port 8000</code>) and reload.
        </p>
      </div>
    );
  }

  if (isLoadingClusters) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <p>Loading clusters...</p>
        </div>
      </div>
    );
  }

  if (!liveClusters || liveClusters.length === 0) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] text-center text-muted-foreground">
        No clusters found.
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="AI Discovery"
        title="Cluster Explorer"
        description="Every cluster below was auto-discovered from raw tickets, scored for business impact, and linked to the deploys that likely caused it."
        actions={
          <FxButton size="sm" variant="outline">
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Cluster settings
          </FxButton>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 h-9 px-3 rounded-md border border-border bg-surface flex-1 min-w-64 max-w-md">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search clusters by title…"
            className="bg-transparent flex-1 text-sm outline-none"
          />
        </div>
        <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-1">
          {SEVS.map((s) => (
            <button
              key={s}
              onClick={() => setSev(s)}
              className={`h-7 px-3 text-xs rounded font-semibold uppercase tracking-wider ${sev === s ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="text-xs text-muted-foreground text-mono ml-auto">
          {filtered.length} of {liveClusters.length} clusters
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedId(c.id)}
                className={`cursor-pointer ${selected?.id === c.id ? "ring-1 ring-primary rounded-lg" : ""}`}
              >
                <ClusterCard cluster={mapCluster(c)} />
              </div>
            ))}
        </div>

        {selected && (
          <Panel
            className="xl:sticky xl:top-20 h-fit"
            title="Cluster Detail"
            action={
              <button
                onClick={() => setSelectedId(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            }
          >
            <div className="space-y-4">
              <div>
                <div className="text-[10px] text-mono text-muted-foreground uppercase tracking-wider">
                  {selected.id}
                </div>
                <h2 className="mt-1 text-lg font-bold leading-tight">{selected.title}</h2>
                <div className="mt-2 flex items-center gap-2">
                  <SeverityBadge severity={selected.severity as any} />
                  <span className="text-xs text-muted-foreground">
                    First seen{" "}
                    {new Date(selected.first_seen_at || selected.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">{selected.summary}</p>

              <div className="grid grid-cols-2 gap-2">
                <Stat label="Tickets" value={selected.ticket_count.toString()} />
                <Stat label="Customers" value={selected.affected_customers.toString()} />
                <Stat
                  label="Monthly cost"
                  value={`$${(selected.monthly_cost_usd / 1000).toFixed(1)}k`}
                  accent
                />
                <Stat
                  label="Confidence"
                  value={selected.confidence ? `${selected.confidence.toFixed(1)}%` : "-"}
                />
              </div>

              {selected.root_cause && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                    Root cause hypothesis
                  </div>
                  <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
                    {selected.root_cause}
                  </div>
                </div>
              )}

              {selected.related_deploy_id && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                    Causal deploy
                  </div>
                  <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-sm">
                    <span
                      className="h-2 w-2 rounded-full bg-secondary"
                      style={{ boxShadow: "0 0 6px var(--secondary)" }}
                    />
                    <span className="text-mono">{selected.related_deploy_id}</span>
                  </div>
                </div>
              )}

              {selected.example_titles && selected.example_titles.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                    Example tickets
                  </div>
                  <ul className="space-y-1.5">
                    {selected.example_titles.map((e, i) => (
                      <li
                        key={i}
                        className="text-sm rounded-md border border-border bg-surface px-3 py-2 text-muted-foreground"
                      >
                        <span className="text-foreground">"</span>
                        {e}
                        <span className="text-foreground">"</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <FxButton size="sm" className="flex-1">
                  Propose fix
                </FxButton>
                <FxButton size="sm" variant="outline" className="flex-1">
                  Notify owner
                </FxButton>
              </div>
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2">
      <div className="text-[9px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-0.5 text-base font-bold text-mono ${accent ? "text-primary" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function mapCluster(c: ClusterOut): any {
  return {
    id: c.id,
    title: c.title,
    summary: c.summary,
    severity: c.severity,
    ticketCount: c.ticket_count,
    affectedCustomers: c.affected_customers,
    monthlyCost: c.monthly_cost_usd,
    confidence: c.confidence,
    relatedDeploy: c.related_deploy_id,
  };
}
