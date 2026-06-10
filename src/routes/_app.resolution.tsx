import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { StatusBadge, SeverityBadge } from "@/components/fixloop/SeverityBadge";
import {
  CheckCircle2,
  ArrowRight,
  TrendingDown,
  DollarSign,
  Loader2,
  Play,
  Wand2,
  Calculator,
  Bug,
  ShieldCheck,
  GitBranch,
  Activity,
  FileText,
} from "lucide-react";

import { useAllRecommendations, type RecommendationOut } from "@/hooks/useRecommendations";
import {
  useValidation,
  useRunValidationMutation,
  type ValidationSummary,
} from "@/hooks/useValidation";

import { useEffect } from "react";

export const Route = createFileRoute("/_app/resolution")({
  validateSearch: (search: Record<string, unknown>) => {
    return {
      recId: search.recId as string | undefined,
    };
  },
  head: () => ({ meta: [{ title: "Resolution Center · FixLoop AI" }] }),
  component: ResolutionPage,
});

function ResolutionPage() {
  const search = Route.useSearch();
  const {
    data: recommendations = [],
    isLoading: isLoadingRecs,
    isError: isRecsError,
  } = useAllRecommendations();

  const resolved = recommendations.filter((r) => r.status === "resolved");
  const inProgress = recommendations.filter((r) => r.status === "in_progress");
  const open = recommendations.filter((r) => r.status === "open");

  const [selectedRecId, setSelectedRecId] = useState<string | null>(search.recId || null);

  useEffect(() => {
    if (search.recId) {
      setSelectedRecId(search.recId);
    }
  }, [search.recId]);

  const selectedRec = recommendations.find((r) => r.id === selectedRecId);

  if (isRecsError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-lg font-bold text-critical">Cannot load recommendations</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Supabase connection failed. Check{" "}
          <code className="text-mono">VITE_SUPABASE_URL</code> and{" "}
          <code className="text-mono">VITE_SUPABASE_ANON_KEY</code> in your{" "}
          <code className="text-mono">.env</code> file.
        </p>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="p-8 space-y-6 pb-32">
        <PageHeader
          eyebrow="Close the loop"
          title="Resolution Center"
          description="Track fixes from proposal to verified deflection. Every resolution closes the loop with measured ticket reduction and recovered revenue."
        />
        <div className="flex flex-col items-center justify-center min-h-[40vh] text-center text-muted-foreground">
          No recommendations generated yet. Head to the AI Command Center to investigate clusters.
        </div>
      </div>
    );
  }

  if (isLoadingRecs) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading resolutions...</span>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 pb-32">
      <PageHeader
        eyebrow="Close the loop"
        title="Resolution Center"
        description="Track fixes from proposal to verified deflection. Every resolution closes the loop with measured ticket reduction and recovered revenue."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <StatPill label="Open Fixes" value={open.length} tone="critical" />
        <StatPill label="In Progress" value={inProgress.length} tone="warning" />
        <StatPill label="Loop Closures (Q2)" value={resolved.length} tone="secondary" />
      </div>

      {selectedRec ? (
        <RecommendationDetail rec={selectedRec} onBack={() => setSelectedRecId(null)} />
      ) : (
        <>
          <Panel
            title="Loop Closures"
            subtitle="Verified before/after ticket volume per shipped fix"
          >
            {resolved.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No loop closures yet. Ship a fix and run validation to see it here.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {resolved.map((r) => (
                  <div
                    key={r.id}
                    className="rounded-lg border border-secondary/30 bg-secondary/5 p-5 relative overflow-hidden"
                  >
                    <div
                      className="absolute inset-x-0 top-0 h-px"
                      style={{
                        background:
                          "linear-gradient(90deg, transparent, var(--secondary), transparent)",
                      }}
                    />
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[10px] text-mono text-muted-foreground uppercase tracking-wider">
                          {r.cluster_id}
                        </div>
                        <h3 className="mt-1 text-base font-bold leading-tight">{r.title}</h3>
                      </div>
                      <div
                        className="h-9 w-9 rounded-full bg-secondary/20 flex items-center justify-center cursor-pointer"
                        onClick={() => setSelectedRecId(r.id)}
                      >
                        <CheckCircle2 className="h-5 w-5 text-secondary" />
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                      <div className="rounded-md border border-border bg-card p-3 text-center">
                        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          Before fix
                        </div>
                        <div className="mt-1 text-2xl font-bold text-mono text-[color:var(--critical)]">
                          {r.before_ticket_count || 0}
                        </div>
                        <div className="text-[10px] text-muted-foreground">tickets / mo</div>
                      </div>
                      <ArrowRight className="h-5 w-5 text-secondary" />
                      <div className="rounded-md border border-secondary/40 bg-secondary/10 p-3 text-center">
                        <div className="text-[10px] uppercase tracking-wider text-secondary">
                          After fix
                        </div>
                        <div className="mt-1 text-2xl font-bold text-mono text-secondary">
                          {r.after_ticket_count || 0}
                        </div>
                        <div className="text-[10px] text-muted-foreground">tickets / mo</div>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center gap-2">
                        <TrendingDown className="h-4 w-4 text-secondary" />
                        <span className="font-semibold text-mono">
                          {r.actual_reduction_pct || r.expected_reduction_pct || 0}%
                        </span>{" "}
                        deflection
                      </div>
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-primary" />
                        <span className="font-semibold text-mono text-primary">
                          $
                          {((r.actual_recovery_usd || r.expected_recovery_usd || 0) / 1000).toFixed(
                            1,
                          )}
                          k
                        </span>{" "}
                        / mo
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="All Resolutions" subtitle="Pipeline from detection to verified fix">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
                    <th className="text-left font-semibold py-2">Fix Recommendation</th>
                    <th className="text-left font-semibold py-2">Engineering Effort</th>
                    <th className="text-right font-semibold py-2">Reduction</th>
                    <th className="text-right font-semibold py-2">Recovery</th>
                    <th className="text-right font-semibold py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Empty state handled at top level */}
                    recommendations.map((r) => (
                      <tr
                        key={r.id}
                        className="border-b border-border/50 align-top hover:bg-accent/30 cursor-pointer"
                        onClick={() => setSelectedRecId(r.id)}
                      >
                        <td className="py-3 pr-3">
                          <div className="font-medium text-primary hover:underline">{r.title}</div>
                          <div className="text-xs text-muted-foreground text-mono">
                            {r.cluster_id} · {r.id.split("-")[0]}
                          </div>
                        </td>
                        <td className="py-3 pr-3 text-mono text-xs">
                          {r.engineering_effort?.replace("_", " ")}
                        </td>
                        <td className="py-3 text-right text-mono text-secondary font-semibold">
                          {r.expected_reduction_pct}%
                        </td>
                        <td className="py-3 text-right text-mono text-primary font-semibold">
                          ${((r.expected_recovery_usd || 0) / 1000).toFixed(1)}k
                        </td>
                        <td className="py-3 text-right">
                          <StatusBadge status={r.status as any} />
                        </td>
                      </tr>
                    ))
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}

function RecommendationDetail({ rec, onBack }: { rec: RecommendationOut; onBack: () => void }) {
  const { data: validation, isLoading: isLoadingValidation } = useValidation(rec.id);
  const {
    mutate: runValidation,
    isPending: isValidating,
    error: validationError,
  } = useRunValidationMutation();

  const handleValidate = () => {
    runValidation({ recommendationId: rec.id, forceRevalidate: true });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-4">
        <FxButton variant="outline" size="sm" onClick={onBack}>
          ← Back to Resolutions
        </FxButton>
        <div className="text-sm font-mono text-muted-foreground">
          {rec.cluster_id} / {rec.id}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <Panel title="AI Recommended Fix" subtitle="Technical execution plan">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold leading-tight">{rec.title}</h2>
                <div className="mt-2 flex items-center gap-3 flex-wrap">
                  <SeverityBadge severity={(rec.priority as any) || "medium"} />
                  <span className="text-xs text-muted-foreground text-mono">
                    Effort: {rec.engineering_effort}
                  </span>
                  <span className="text-xs text-muted-foreground text-mono text-primary">
                    Confidence: {rec.confidence_score}%
                  </span>
                </div>
              </div>
              <div className="prose prose-sm prose-invert max-w-none text-muted-foreground">
                <p>{rec.description}</p>
              </div>

              {/* Jira Ticket Section */}
              <div className="mt-8 pt-6 border-t border-border">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground mb-4">
                  <Bug className="h-4 w-4 text-primary" /> Jira Ticket Draft
                </div>
                <div className="rounded-md border border-border bg-surface p-5">
                  <h3 className="font-semibold text-lg">{rec.jira_title || rec.title}</h3>
                  <div className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
                    {rec.jira_description || rec.description}
                  </div>

                  {rec.jira_acceptance_criteria && rec.jira_acceptance_criteria.length > 0 && (
                    <div className="mt-4">
                      <div className="text-xs font-semibold uppercase tracking-wider text-foreground mb-2">
                        Acceptance Criteria
                      </div>
                      <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
                        {rec.jira_acceptance_criteria.map((ac, i) => (
                          <li key={i}>{ac}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="mt-4 flex gap-2">
                    <FxButton size="sm" variant="cyber">
                      <Bug className="h-3.5 w-3.5" /> Create in Jira
                    </FxButton>
                  </div>
                </div>
              </div>
            </div>
          </Panel>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <Panel title="Validation Engine" subtitle="Measure post-ship deflection">
            <div className="space-y-6">
              {isValidating || isLoadingValidation ? (
                <div className="flex flex-col items-center justify-center p-8 space-y-4">
                  <div className="relative">
                    <div
                      className="absolute inset-0 rounded-full animate-ping opacity-20"
                      style={{ background: "var(--secondary)" }}
                    />
                    <div
                      className="h-12 w-12 rounded-full flex items-center justify-center relative z-10"
                      style={{
                        background: "linear-gradient(135deg, var(--secondary), var(--accent))",
                      }}
                    >
                      <Calculator className="h-6 w-6 text-primary-foreground animate-pulse" />
                    </div>
                  </div>
                  <div className="text-center space-y-2">
                    <div className="flex items-center gap-2 justify-center text-sm font-semibold text-secondary">
                      <Loader2 className="h-4 w-4 animate-spin" /> Calculating Validation...
                    </div>
                    <div className="text-xs text-muted-foreground animate-pulse">
                      Building summary
                    </div>
                  </div>
                </div>
              ) : !rec.id || !validation ? (
                <div className="text-center py-8">
                  <ShieldCheck className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                  <p className="text-sm text-muted-foreground mb-6">
                    Has this fix been shipped? Run the validation engine to measure actual
                    deflection and loop closure.
                  </p>
                  <FxButton size="sm" variant="cyber" onClick={handleValidate}>
                    <Play className="h-3.5 w-3.5" /> Validate Fix
                  </FxButton>
                </div>
              ) : (
                <>
                  <ValidationScorecard validation={validation} />
                  {validationError && (
                    <div className="text-xs text-critical p-3 border border-critical/30 rounded bg-critical/10">
                      {validationError.message}
                    </div>
                  )}
                  <div className="pt-4 flex gap-2 border-t border-border">
                    <FxButton
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={handleValidate}
                    >
                      Re-run Validation
                    </FxButton>
                  </div>
                </>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function ValidationScorecard({ validation }: { validation: ValidationSummary }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">Validation Status</div>
        <StatusBadge status={validation.status as any} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-md border border-border bg-surface p-3">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Before Fix
          </div>
          <div className="mt-1 text-xl font-bold text-[color:var(--critical)] text-mono">
            {validation.before_ticket_count}
          </div>
          <div className="text-[10px] text-muted-foreground">tickets / mo</div>
          <div className="mt-2 text-xs font-semibold text-[color:var(--critical)]">
            ${(validation.before_revenue_risk / 1000).toFixed(1)}k risk
          </div>
        </div>
        <div className="rounded-md border border-secondary/30 bg-secondary/10 p-3">
          <div className="text-[10px] uppercase tracking-wider text-secondary">After Fix</div>
          <div className="mt-1 text-xl font-bold text-secondary text-mono">
            {validation.after_ticket_count}
          </div>
          <div className="text-[10px] text-muted-foreground">tickets / mo</div>
          <div className="mt-2 text-xs font-semibold text-secondary">
            ${(validation.after_revenue_risk / 1000).toFixed(1)}k risk
          </div>
        </div>
      </div>

      <div className="rounded-md border border-primary/30 bg-primary/5 p-4 text-center">
        <div className="text-[10px] uppercase tracking-wider text-primary font-semibold mb-1">
          Deflection Achieved
        </div>
        <div className="text-4xl font-bold text-mono flex items-center justify-center gap-2">
          <TrendingDown className="h-6 w-6 text-primary" /> {validation.deflection_pct.toFixed(1)}%
        </div>
        <div className="mt-3 text-sm text-muted-foreground">
          Recovered{" "}
          <span className="text-foreground font-mono font-bold">
            ${validation.revenue_recovered_usd.toLocaleString()}
          </span>{" "}
          / mo
        </div>
      </div>
    </div>
  );
}

function StatPill({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "critical" | "warning" | "secondary";
}) {
  const color = {
    critical: "var(--critical)",
    warning: "var(--warning)",
    secondary: "var(--secondary)",
  }[tone];
  return (
    <div className="rounded-lg border border-border bg-card p-5 relative overflow-hidden">
      <div className="absolute inset-y-0 left-0 w-1" style={{ background: color }} />
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-3xl font-bold text-mono" style={{ color }}>
        {value}
      </div>
    </div>
  );
}
