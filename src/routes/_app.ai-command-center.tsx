import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { copilotSuggestions } from "@/lib/mock-data";
import {
  BrainCircuit,
  Sparkles,
  Send,
  ChevronDown,
  ChevronRight,
  TrendingDown,
  DollarSign,
  Users,
  GitBranch,
  ShieldCheck,
  Wand2,
  FileText,
  Bug,
  Activity,
  Loader2,
  Database,
  Search,
} from "lucide-react";

import { useClusters } from "@/hooks/useClusters";
import {
  useInvestigationByCluster,
  useRunInvestigationMutation,
  type EvidenceOut,
} from "@/hooks/useInvestigations";
import { useRecommendations, useGenerateRecommendationMutation } from "@/hooks/useRecommendations";
import { useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/ai-command-center")({
  head: () => ({ meta: [{ title: "AI Command Center · FixLoop AI" }] }),
  component: AICommandCenterPage,
});

function AICommandCenterPage() {
  const navigate = useNavigate({ from: "/ai-command-center" });
  const {
    data: clusters = [],
    isLoading: isLoadingClusters,
    isError: isClustersError,
  } = useClusters(
    1,
    10,
    undefined,
    "open",
  );
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  // Set first cluster as default if none selected
  useEffect(() => {
    if (clusters.length > 0 && !selectedClusterId) {
      setSelectedClusterId(clusters[0].id);
    }
  }, [clusters, selectedClusterId]);

  const { data: inv, isLoading: isLoadingInv } = useInvestigationByCluster(selectedClusterId || "");
  const {
    mutate: runInv,
    isPending: isRunningInv,
    error: runError,
  } = useRunInvestigationMutation();

  const { data: rec, isLoading: isLoadingRec } = useRecommendations(inv?.id);
  const { mutateAsync: generateRec, isPending: isGeneratingRec } =
    useGenerateRecommendationMutation();

  const [openEvidence, setOpenEvidence] = useState<string | null>(null);
  const [copilotOpen, setCopilotOpen] = useState(true);
  const [query, setQuery] = useState("");

  const handleGenerate = () => {
    if (selectedClusterId) {
      runInv({ clusterId: selectedClusterId, forceRefresh: true });
    }
  };

  const handleGenerateRecommendation = async () => {
    if (inv && selectedClusterId) {
      const result = await generateRec({ investigationId: inv.id, clusterId: selectedClusterId });
      if (result) {
        navigate({ to: "/resolution", search: { recId: result.id } });
      }
    }
  };

  const handleProceedToResolution = () => {
    if (rec) {
      navigate({ to: "/resolution", search: { recId: rec.id } });
    }
  };

  if (isClustersError) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-lg font-bold text-critical">AI Service Unreachable</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Cannot connect to{" "}
          <code className="text-mono text-primary">
            {import.meta.env.VITE_API_URL || "http://localhost:8000"}
          </code>.
          Start the FastAPI backend with{" "}
          <code className="text-mono">uvicorn main:app --reload --port 8000</code> and reload.
        </p>
      </div>
    );
  }

  if (!clusters || clusters.length === 0) {
    return (
      <div className="p-8">
        <PageHeader
          eyebrow="Autonomous Agent · Live"
          title="AI Command Center"
          description="A continuous root-cause investigation across every ticket, deploy, and customer signal."
        />
        <div className="mt-12 text-center text-muted-foreground">
          No open clusters available for investigation.
        </div>
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

  return (
    <div className="relative">
      <div className="p-8 space-y-6 pb-32">
        <PageHeader
          eyebrow="Autonomous Agent · Live"
          title="AI Command Center"
          description="A continuous root-cause investigation across every ticket, deploy, and customer signal — explainable, traceable, and ready to act."
          actions={
            <>
              <FxButton size="sm" variant="outline">
                <FileText className="h-3.5 w-3.5" />
                Executive summary
              </FxButton>
              <FxButton
                size="sm"
                variant="cyber"
                onClick={handleGenerate}
                disabled={isRunningInv || !selectedClusterId}
              >
                <Wand2 className="h-3.5 w-3.5" />
                {isRunningInv ? "Investigating..." : "Generate investigation"}
              </FxButton>
            </>
          }
        />

        {runError && (
          <div className="rounded-md border border-critical/50 bg-critical/10 p-4 text-sm text-critical">
            <strong>Investigation failed:</strong> {runError.message}
          </div>
        )}

        {/* Investigation switcher */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {clusters.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedClusterId(c.id)}
              className={`h-9 px-3 rounded-md border text-xs font-semibold tracking-tight whitespace-nowrap flex items-center gap-2 transition-colors ${
                selectedClusterId === c.id
                  ? "border-primary/60 bg-primary/10 text-foreground"
                  : "border-border bg-surface text-muted-foreground hover:text-foreground hover:border-primary/30"
              }`}
            >
              <span className="text-mono text-[10px]">
                {c.id.split("-")[0]}-{c.id.slice(-4)}
              </span>
              <span>{c.title}</span>
            </button>
          ))}
        </div>

        {isRunningInv || isLoadingInv ? (
          <AIThinkingLoader />
        ) : !selectedClusterId || !inv ? (
          <div className="flex flex-col items-center justify-center min-h-[40vh] border border-border rounded-lg bg-surface/50 border-dashed">
            <BrainCircuit className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-semibold">No Investigation Found</h3>
            <p className="text-sm text-muted-foreground mt-2 mb-6 max-w-sm text-center">
              The AI has not yet analyzed this cluster. Generate a deep investigation to find the
              root cause.
            </p>
            <FxButton variant="cyber" onClick={handleGenerate}>
              <Sparkles className="h-4 w-4" />
              Start AI Investigation
            </FxButton>
          </div>
        ) : (
          <>
            {/* A. Hero Root Cause Card */}
            <div className="relative overflow-hidden rounded-xl border border-primary/40 bg-surface/80 p-8 backdrop-blur-xl shadow-2xl">
              <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/20 blur-3xl opacity-50" />
              <div className="absolute -left-20 -bottom-20 h-64 w-64 rounded-full bg-secondary/20 blur-3xl opacity-50" />
              
              <div className="relative z-10 flex flex-col lg:flex-row gap-8 items-start justify-between">
                <div className="flex-1 space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg flex items-center justify-center border border-primary/50 shadow-[0_0_15px_rgba(var(--primary-rgb),0.3)]" style={{ background: "var(--gradient-cyber)" }}>
                      <BrainCircuit className="h-5 w-5 text-primary-foreground animate-pulse" />
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.2em] text-primary font-bold">FixLoop Reasoner Active</div>
                      <div className="text-sm font-mono text-muted-foreground mt-0.5">ID: {inv.id.split("-")[0]} · CLUSTER: {inv.cluster_id}</div>
                    </div>
                  </div>

                  <div>
                    <h2 className="text-3xl font-extrabold leading-tight tracking-tight text-foreground" style={{ textShadow: "0 0 20px rgba(255,255,255,0.1)" }}>
                      {inv.root_cause}
                    </h2>
                    <div className="mt-4 flex items-center gap-3 flex-wrap">
                      <SeverityBadge severity={inv.impact_level as any} />
                      <div className="h-1 w-1 rounded-full bg-border" />
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Users className="h-4 w-4" />
                        <span className="font-mono text-foreground font-semibold">{inv.affected_customers.toLocaleString()}</span> affected
                      </div>
                      <div className="h-1 w-1 rounded-full bg-border" />
                      <div className="flex items-center gap-1.5 text-sm text-critical">
                        <DollarSign className="h-4 w-4" />
                        Revenue Risk: <span className="font-mono font-bold">${(inv.revenue_impact_usd / 1000).toFixed(1)}k/mo</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="shrink-0 flex flex-col items-center justify-center p-6 rounded-2xl bg-black/40 border border-primary/20 backdrop-blur-md shadow-inner relative group">
                  <div className="absolute inset-0 bg-primary/5 rounded-2xl transition-opacity duration-500 opacity-0 group-hover:opacity-100" />
                  <AdvancedConfidenceRing value={inv.confidence} />
                  <div className="mt-4 text-center relative z-10">
                    <div className="text-[10px] uppercase tracking-widest text-primary/80 font-semibold">Model Confidence</div>
                    <div className="text-xs text-muted-foreground mt-0.5">Cross-source consensus</div>
                  </div>
                </div>
              </div>
              
              {/* Deploy Correlation Sparkline underneath */}
              {inv.deploy_correlation && (
                <div className="relative z-10 mt-8 pt-6 border-t border-border/50">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-secondary" />
                      <span className="text-xs uppercase tracking-wider font-semibold text-secondary">Causal Deploy Identified: <span className="font-mono text-foreground">{inv.deploy_correlation.version}</span></span>
                    </div>
                    <div className="text-xs text-mono bg-secondary/10 text-secondary px-2 py-0.5 rounded border border-secondary/20">
                      {Math.round(inv.deploy_correlation.correlation * 100)}% Correlation
                    </div>
                  </div>
                  <DeploySparkline />
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
              {/* B. Explainability */}
              <Panel
                title="Explainability Engine"
                subtitle="Why the agent reached this conclusion"
                className="border-primary/20 bg-surface/40 backdrop-blur-sm"
              >
                <div className="space-y-8">
                  {/* Reasoning Chain */}
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-primary/80 font-bold mb-4 flex items-center gap-2">
                      <Sparkles className="h-3 w-3" />
                      Neural Reasoning Pathway
                    </div>
                    <div className="relative pl-3 border-l border-primary/20 space-y-6">
                      {inv.reasoning_steps.map((r, i) => (
                        <div key={i} className="relative">
                          <div className="absolute -left-[17px] top-1 h-2 w-2 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
                          <div className="text-sm text-foreground/90 leading-relaxed pl-4">{r}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Evidence Trail */}
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-primary/80 font-bold mb-4 flex items-center gap-2">
                      <Database className="h-3 w-3" />
                      Forensic Trace
                    </div>
                    <div className="space-y-3">
                      {inv.evidence.map((e) => {
                        const open = openEvidence === e.id;
                        return (
                          <div key={e.id} className="rounded-lg border border-border/60 bg-surface/50 overflow-hidden transition-all duration-300 hover:border-primary/40">
                            <button
                              onClick={() => setOpenEvidence(open ? null : e.id)}
                              className="w-full flex items-center gap-4 px-4 py-3 text-left"
                            >
                              <div className="shrink-0 relative">
                                {open && <div className="absolute inset-0 bg-primary blur-md opacity-40 rounded-full" />}
                                <EvidenceIcon type={e.evidence_type} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold truncate text-foreground/90">{e.title}</div>
                                <div className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">
                                  {e.evidence_type.replace(/_/g, " ")}
                                </div>
                              </div>
                              <div className="shrink-0 text-right">
                                <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Weight</div>
                                <div className="text-xs font-mono font-bold text-primary">
                                  {(e.weight * 100).toFixed(0)}%
                                </div>
                              </div>
                            </button>
                            {open && (
                              <div className="px-4 pb-4 pt-2 border-t border-border/40 bg-black/20">
                                <p className="text-sm text-muted-foreground leading-relaxed">{e.detail}</p>
                                <div className="mt-4 flex items-center gap-3">
                                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground shrink-0">Impact Score</div>
                                  <div className="h-1.5 flex-1 rounded-full bg-accent overflow-hidden">
                                    <div
                                      className="h-full rounded-full"
                                      style={{
                                        width: `${e.weight * 100}%`,
                                        background: "var(--gradient-cyber)",
                                      }}
                                    />
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </Panel>

              {/* D. Fix Validation Simulator */}
              {inv.simulation ? (
                <Panel 
                  title="Simulation Forecast" 
                  subtitle="Projected outcome if a fix is shipped"
                  className="border-secondary/20 bg-surface/40 backdrop-blur-sm"
                >
                  <div className="flex flex-col gap-8">
                    
                    <div className="rounded-xl border border-secondary/30 bg-secondary/5 p-6 relative overflow-hidden group">
                      <div className="absolute inset-0 bg-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
                      <div className="relative z-10 flex items-center justify-between">
                        <div>
                          <div className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-1">
                            Predicted Revenue Recovery
                          </div>
                          <div className="text-5xl font-extrabold text-mono text-foreground" style={{ textShadow: "0 0 20px rgba(var(--secondary-rgb), 0.3)" }}>
                            ${inv.simulation.recovered_usd.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground mt-2 font-medium">
                            per month at current trajectory
                          </div>
                        </div>
                        <div className="h-16 w-16 rounded-full border-2 border-secondary/30 flex items-center justify-center bg-secondary/10">
                          <TrendingDown className="h-8 w-8 text-secondary" />
                        </div>
                      </div>
                      
                      <div className="relative z-10 mt-8">
                        <div className="flex justify-between text-[10px] uppercase tracking-widest font-bold mb-2">
                          <span className="text-critical">Baseline Loss</span>
                          <span className="text-secondary">Predicted Recovery</span>
                        </div>
                        <div className="h-3 w-full bg-critical/20 rounded-full overflow-hidden flex">
                          <div className="h-full bg-critical" style={{ width: `${100 - inv.simulation.deflection_pct}%` }} />
                          <div className="h-full bg-secondary shadow-[0_0_10px_var(--secondary)] relative" style={{ width: `${inv.simulation.deflection_pct}%` }}>
                            <div className="absolute inset-0 bg-white/20 animate-pulse" />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                      <div className="bg-surface/50 border border-border/50 rounded-xl p-5 text-center">
                        <div className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-2">Before Fix</div>
                        <div className="text-3xl font-mono font-bold text-critical">{inv.simulation.before_ticket_count}</div>
                        <div className="text-xs text-muted-foreground mt-1">tickets / mo</div>
                      </div>
                      
                      <div className="flex flex-col items-center justify-center">
                        <div className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-2">Deflection</div>
                        <div className="flex items-center gap-2 text-2xl font-mono font-bold text-secondary">
                          <TrendingDown className="h-5 w-5" />
                          {inv.simulation.deflection_pct}%
                        </div>
                      </div>

                      <div className="bg-secondary/10 border border-secondary/30 rounded-xl p-5 text-center shadow-[0_0_15px_rgba(var(--secondary-rgb),0.1)]">
                        <div className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-2">After Fix</div>
                        <div className="text-3xl font-mono font-bold text-foreground">{inv.simulation.after_ticket_count}</div>
                        <div className="text-xs text-secondary mt-1">tickets / mo</div>
                      </div>
                    </div>

                  </div>
                </Panel>
              ) : <div />}
            </div>

            {/* F. Action Area to Route to Resolution Center */}
            <div className="flex items-center justify-end gap-4 pt-4">
              {rec ? (
                <FxButton variant="cyber" onClick={handleProceedToResolution}>
                  Proceed To Resolution
                  <ChevronRight className="h-4 w-4 ml-1" />
                </FxButton>
              ) : (
                <FxButton
                  variant="cyber"
                  onClick={handleGenerateRecommendation}
                  disabled={isGeneratingRec}
                >
                  {isGeneratingRec ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating Fix Recommendation...
                    </>
                  ) : (
                    <>
                      <Wand2 className="h-4 w-4 mr-2" />
                      Generate Fix Recommendation
                    </>
                  )}
                </FxButton>
              )}
            </div>
          </>
        )}
      </div>

      {/* E. Floating Copilot */}
      <div className="fixed bottom-6 right-6 z-30 w-[360px]">
        {copilotOpen ? (
          <div
            className="rounded-lg border border-primary/30 bg-card shadow-2xl overflow-hidden"
            style={{ boxShadow: "var(--shadow-elevated), var(--shadow-glow)" }}
          >
            <div
              className="flex items-center gap-2 px-4 py-3 border-b border-border"
              style={{ background: "var(--gradient-cyber)" }}
            >
              <BrainCircuit className="h-4 w-4 text-primary-foreground" />
              <div className="text-sm font-bold text-primary-foreground">FixLoop Copilot</div>
              <span className="ml-auto text-[10px] text-mono uppercase tracking-wider text-primary-foreground/80">
                online
              </span>
              <button
                onClick={() => setCopilotOpen(false)}
                className="text-primary-foreground/80 hover:text-primary-foreground text-xs"
              >
                —
              </button>
            </div>
            <div className="p-3 max-h-72 overflow-y-auto space-y-2 bg-background/40">
              <div className="rounded-md bg-surface border border-border p-3 text-sm">
                <div className="text-[10px] uppercase tracking-wider text-primary font-semibold mb-1">
                  Copilot
                </div>
                {inv ? (
                  <>
                    Investigating{" "}
                    <span className="text-mono text-foreground">{inv.cluster_id}</span> — the spike
                    correlates with deploy{" "}
                    <span className="text-mono">{inv.deploy_correlation?.version || "None"}</span>{" "}
                    at{" "}
                    <span className="text-mono text-primary">
                      {Math.round((inv.deploy_correlation?.correlation || 0) * 100)}%
                    </span>
                    . What should I do next?
                  </>
                ) : (
                  <>I am ready to run an investigation whenever you select a cluster.</>
                )}
              </div>
              <div className="space-y-1.5">
                {copilotSuggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => setQuery(s)}
                    className="w-full text-left text-xs rounded-md border border-border bg-surface px-2.5 py-1.5 hover:border-primary/40 hover:text-foreground text-muted-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="p-3 border-t border-border flex items-center gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask the agent…"
                className="flex-1 h-9 px-3 rounded-md bg-surface border border-border text-sm outline-none focus:border-primary/50"
              />
              <FxButton size="sm" variant="cyber">
                <Send className="h-3.5 w-3.5" />
              </FxButton>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setCopilotOpen(true)}
            className="ml-auto flex items-center gap-2 h-12 px-4 rounded-full text-primary-foreground font-semibold shadow-lg"
            style={{ background: "var(--gradient-cyber)", boxShadow: "var(--shadow-glow)" }}
          >
            <BrainCircuit className="h-4 w-4" />
            Ask Copilot
          </button>
        )}
      </div>
    </div>
  );
}

function AIThinkingLoader() {
  const states = [
    { label: "Loading tickets", icon: Database },
    { label: "Correlating deployments", icon: GitBranch },
    { label: "Building evidence", icon: Search },
    { label: "Generating root cause", icon: BrainCircuit },
  ];
  const [step, setStep] = useState(0);

  useEffect(() => {
    const int = setInterval(() => {
      setStep((s) => Math.min(s + 1, states.length - 1));
    }, 3000);
    return () => clearInterval(int);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] border border-border rounded-lg bg-surface/50 p-8">
      <div className="relative mb-8">
        <div
          className="absolute inset-0 rounded-full animate-ping opacity-20"
          style={{ background: "var(--primary)" }}
        />
        <div
          className="h-16 w-16 rounded-full flex items-center justify-center relative z-10"
          style={{ background: "var(--gradient-cyber)" }}
        >
          <BrainCircuit className="h-8 w-8 text-primary-foreground animate-pulse" />
        </div>
      </div>

      <div className="space-y-4 w-full max-w-sm">
        {states.map((s, i) => {
          const active = i === step;
          const done = i < step;
          const Icon = s.icon;
          return (
            <div
              key={i}
              className={`flex items-center gap-3 transition-opacity duration-500 ${active || done ? "opacity-100" : "opacity-30"}`}
            >
              <div
                className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 border ${done ? "bg-primary/20 border-primary text-primary" : active ? "bg-accent border-accent-foreground/20 text-foreground" : "bg-surface border-border text-muted-foreground"}`}
              >
                {done ? (
                  <ShieldCheck className="h-3.5 w-3.5" />
                ) : active ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Icon className="h-3 w-3" />
                )}
              </div>
              <span
                className={`text-sm ${active ? "font-semibold text-primary" : done ? "text-foreground" : "text-muted-foreground"}`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// (Unused components removed during redesign)

function DeploySparkline() {
  // A visual representation of tickets spiking post-deploy
  return (
    <div className="h-12 w-full flex items-end gap-1 relative">
      <div className="absolute left-1/4 top-0 bottom-0 w-px bg-secondary border-r border-secondary/50 shadow-[0_0_10px_var(--secondary)] z-0" />
      <div className="absolute left-[24.5%] -top-2 bg-secondary text-black text-[8px] font-bold px-1 rounded z-10">DEPLOY</div>
      
      {/* Before Deploy */}
      {[10, 15, 12, 18, 14, 16, 12].map((h, i) => (
        <div key={`pre-${i}`} className="flex-1 bg-surface border border-border/50 rounded-t" style={{ height: `${h}%` }} />
      ))}
      
      {/* After Deploy Spike */}
      {[45, 60, 85, 95, 100, 90, 85, 80, 95, 85, 90, 100].map((h, i) => (
        <div key={`post-${i}`} className="flex-1 bg-primary/40 border border-primary/60 rounded-t shadow-[0_0_8px_rgba(var(--primary-rgb),0.5)]" style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

function AdvancedConfidenceRing({ value }: { value: number }) {
  const rOuter = 46;
  const rInner = 36;
  const cOuter = 2 * Math.PI * rOuter;
  const cInner = 2 * Math.PI * rInner;
  
  const offsetOuter = cOuter - (value / 100) * cOuter;
  // Inner ring spins completely or shows a different metric, here just a decorative dash
  const offsetInner = cInner * 0.25;

  return (
    <div className="relative flex items-center justify-center">
      <div className="absolute inset-0 rounded-full bg-primary/10 blur-xl animate-pulse" />
      <svg width="120" height="120" viewBox="0 0 120 120" className="relative z-10">
        <defs>
          <linearGradient id="cyber-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--primary)" />
            <stop offset="100%" stopColor="var(--secondary)" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Outer Ring Background */}
        <circle cx="60" cy="60" r={rOuter} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
        {/* Inner Ring Background */}
        <circle cx="60" cy="60" r={rInner} fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="2" strokeDasharray="4 4" />

        {/* Outer Ring Progress */}
        <circle
          cx="60"
          cy="60"
          r={rOuter}
          fill="none"
          stroke="url(#cyber-gradient)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={cOuter}
          strokeDashoffset={offsetOuter}
          transform="rotate(-90 60 60)"
          filter="url(#glow)"
        />

        {/* Inner Ring Decorative */}
        <circle
          cx="60"
          cy="60"
          r={rInner}
          fill="none"
          stroke="var(--secondary)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={cInner}
          strokeDashoffset={offsetInner}
          transform="rotate(180 60 60)"
          className="animate-[spin_10s_linear_infinite] origin-center"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-2xl font-bold text-mono text-foreground" style={{ textShadow: "0 0 10px rgba(var(--primary-rgb), 0.5)" }}>
          {value.toFixed(1)}<span className="text-sm text-primary">%</span>
        </div>
      </div>
    </div>
  );
}

function EvidenceIcon({ type }: { type: string }) {
  const map: Record<string, any> = {
    deploy_correlation: GitBranch,
    ticket_pattern: Activity,
    customer_impact: Users,
    similar_ticket: BrainCircuit,
  };
  const Icon = map[type] || FileText;
  return (
    <div className="h-7 w-7 rounded-md border border-primary/30 bg-primary/10 flex items-center justify-center text-primary shrink-0">
      <Icon className="h-3.5 w-3.5" />
    </div>
  );
}
