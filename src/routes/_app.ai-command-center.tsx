import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { aiInvestigations, copilotSuggestions } from "@/lib/mock-data";
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
} from "lucide-react";

export const Route = createFileRoute("/_app/ai-command-center")({
  head: () => ({ meta: [{ title: "AI Command Center · FixLoop AI" }] }),
  component: AICommandCenterPage,
});

function AICommandCenterPage() {
  const [selectedId, setSelectedId] = useState(aiInvestigations[0].id);
  const inv = aiInvestigations.find((i) => i.id === selectedId)!;
  const [openEvidence, setOpenEvidence] = useState<string | null>(inv.evidence[0]?.id ?? null);
  const [copilotOpen, setCopilotOpen] = useState(true);
  const [query, setQuery] = useState("");

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
              <FxButton size="sm" variant="cyber">
                <Wand2 className="h-3.5 w-3.5" />
                Generate fix plan
              </FxButton>
            </>
          }
        />

        {/* Investigation switcher */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {aiInvestigations.map((i) => (
            <button
              key={i.id}
              onClick={() => {
                setSelectedId(i.id);
                setOpenEvidence(i.evidence[0]?.id ?? null);
              }}
              className={`h-9 px-3 rounded-md border text-xs font-semibold tracking-tight whitespace-nowrap flex items-center gap-2 ${selectedId === i.id ? "border-primary/60 bg-primary/10 text-foreground" : "border-border bg-surface text-muted-foreground hover:text-foreground"}`}
            >
              <span className="text-mono text-[10px]">{i.id}</span>
              <span>{i.rootCause}</span>
              <span className="text-mono text-[10px] text-primary">{i.confidence}%</span>
            </button>
          ))}
        </div>

        {/* A. Investigation Panel */}
        <Panel
          title="AI Investigation"
          subtitle="Live root-cause analysis"
          action={
            <div className="flex items-center gap-2 text-[10px] text-mono uppercase tracking-wider text-muted-foreground">
              <span
                className="h-1.5 w-1.5 rounded-full bg-secondary animate-pulse"
                style={{ boxShadow: "0 0 6px var(--secondary)" }}
              />
              Analyzing 12,480 tickets
            </div>
          }
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-7 space-y-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Detected root cause
              </div>
              <div className="flex items-start gap-3">
                <div
                  className="h-9 w-9 rounded-md flex items-center justify-center shrink-0"
                  style={{ background: "var(--gradient-cyber)" }}
                >
                  <BrainCircuit className="h-5 w-5 text-primary-foreground" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-xl font-bold leading-tight">{inv.rootCause}</h2>
                  <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                    <SeverityBadge severity={inv.impactLevel} />
                    <span className="text-xs text-muted-foreground text-mono">
                      Cluster {inv.clusterId} · {inv.id}
                    </span>
                  </div>
                </div>
              </div>
              <div className="rounded-md border border-primary/30 bg-primary/5 p-4 flex items-center gap-4">
                <ConfidenceRing value={inv.confidence} />
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-primary font-semibold">
                    Model confidence
                  </div>
                  <div className="text-2xl font-bold text-mono">{inv.confidence}%</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    FixLoop Reasoner v3 · cross-source consensus
                  </div>
                </div>
              </div>
            </div>
            <div className="lg:col-span-5 grid grid-cols-2 gap-3">
              <StatTile
                icon={<Users className="h-4 w-4" />}
                label="Affected customers"
                value={inv.affectedCustomers.toLocaleString()}
              />
              <StatTile
                icon={<DollarSign className="h-4 w-4" />}
                label="Revenue risk / mo"
                value={`$${(inv.revenueImpact / 1000).toFixed(0)}k`}
                accent
              />
              <StatTile
                icon={<GitBranch className="h-4 w-4" />}
                label="Causal deploy"
                value={inv.deployCorrelation.version}
                mono
              />
              <StatTile
                icon={<Activity className="h-4 w-4" />}
                label="Deploy correlation"
                value={`${Math.round(inv.deployCorrelation.correlation * 100)}%`}
              />
            </div>
          </div>
        </Panel>

        {/* B. Explainability + C. Recommendation */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <Panel
            className="xl:col-span-2"
            title="Explainability Engine"
            subtitle="Why the agent reached this conclusion"
          >
            <div className="space-y-4">
              <ol className="space-y-2">
                {inv.reasoning.map((r, i) => (
                  <li key={i} className="flex gap-3 text-sm">
                    <span className="h-5 w-5 rounded-md bg-primary/10 border border-primary/30 text-primary text-[10px] font-bold text-mono flex items-center justify-center shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-muted-foreground">
                      <span className="text-foreground">{r}</span>
                    </span>
                  </li>
                ))}
              </ol>
              <div className="border-t border-border pt-4">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">
                  Evidence trail
                </div>
                <div className="space-y-2">
                  {inv.evidence.map((e) => {
                    const open = openEvidence === e.id;
                    return (
                      <div key={e.id} className="rounded-md border border-border bg-surface">
                        <button
                          onClick={() => setOpenEvidence(open ? null : e.id)}
                          className="w-full flex items-center gap-3 px-3 py-2.5 text-left"
                        >
                          {open ? (
                            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                          )}
                          <EvidenceIcon type={e.type} />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{e.title}</div>
                            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mt-0.5">
                              {e.type.replace(/_/g, " ")}
                            </div>
                          </div>
                          <div className="text-[10px] text-mono text-primary">
                            w {Math.round(e.weight * 100)}
                          </div>
                        </button>
                        {open && (
                          <div className="px-3 pb-3 pt-1 border-t border-border bg-background/40">
                            <p className="text-sm text-muted-foreground">{e.detail}</p>
                            <div className="mt-2 h-1 rounded-full bg-accent overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${e.weight * 100}%`,
                                  background: "var(--gradient-cyber)",
                                }}
                              />
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

          <Panel
            title="AI Recommended Fix"
            subtitle="Ranked by impact × confidence"
            action={<Sparkles className="h-3.5 w-3.5 text-primary" />}
          >
            <div className="space-y-4">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-secondary font-semibold">
                  Recommendation
                </div>
                <h3 className="text-base font-bold leading-tight mt-1">
                  {inv.recommendation.title}
                </h3>
                <p className="text-sm text-muted-foreground mt-1.5">{inv.recommendation.detail}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <MiniMetric
                  label="Ticket reduction"
                  value={`${inv.recommendation.expectedReduction}%`}
                  accent
                />
                <MiniMetric
                  label="Revenue recovery"
                  value={`$${(inv.recommendation.expectedRecovery / 1000).toFixed(0)}k`}
                  accent
                />
                <MiniMetric label="Suggested owner" value={inv.recommendation.owner} />
                <MiniMetric label="ETA" value={inv.recommendation.eta} />
              </div>
              <div className="flex gap-2">
                <FxButton size="sm" className="flex-1">
                  <Bug className="h-3.5 w-3.5" />
                  Create Jira ticket
                </FxButton>
                <FxButton size="sm" variant="outline">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Approve
                </FxButton>
              </div>
            </div>
          </Panel>
        </div>

        {/* D. Fix Validation Simulator */}
        <Panel
          title="Fix Validation Simulator"
          subtitle="Projected outcome if the recommended fix ships"
          action={
            <FxButton size="sm" variant="outline">
              Re-run simulation
            </FxButton>
          }
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-3">
              <CompareCard
                label="Before fix"
                value={inv.simulation.before}
                sub="tickets / cycle"
                tone="critical"
              />
            </div>
            <div className="lg:col-span-2 flex flex-col items-center gap-2">
              <ArrowFlow />
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Projected change
              </div>
              <div className="text-3xl font-bold text-mono text-primary flex items-center gap-1">
                <TrendingDown className="h-5 w-5" />
                {inv.simulation.deflection}%
              </div>
              <div className="text-[10px] text-muted-foreground">deflection</div>
            </div>
            <div className="lg:col-span-3">
              <CompareCard
                label="After fix"
                value={inv.simulation.after}
                sub="tickets / cycle"
                tone="secondary"
              />
            </div>
            <div className="lg:col-span-4 rounded-md border border-secondary/30 bg-secondary/5 p-4">
              <div className="text-[10px] uppercase tracking-wider text-secondary font-semibold">
                Revenue recovered
              </div>
              <div className="mt-1 text-3xl font-bold text-mono">
                ${inv.simulation.recovered.toLocaleString()}
              </div>
              <div className="text-xs text-muted-foreground">per month at current trajectory</div>
              <div className="mt-3 h-1.5 rounded-full bg-accent overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${inv.simulation.deflection}%`,
                    background: "var(--gradient-cyber)",
                  }}
                />
              </div>
              <div className="mt-1.5 flex items-center justify-between text-[10px] text-mono text-muted-foreground">
                <span>baseline</span>
                <span>projected</span>
              </div>
            </div>
          </div>
        </Panel>
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
                Investigating <span className="text-mono text-foreground">{inv.clusterId}</span> —
                the spike correlates with deploy{" "}
                <span className="text-mono">{inv.deployCorrelation.version}</span> at{" "}
                <span className="text-mono text-primary">
                  {Math.round(inv.deployCorrelation.correlation * 100)}%
                </span>
                . Want me to draft a Jira ticket?
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

function StatTile({
  icon,
  label,
  value,
  accent,
  mono,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
        <span className="text-primary">{icon}</span>
        {label}
      </div>
      <div
        className={`mt-1 text-lg font-bold ${accent ? "text-primary" : ""} ${mono ? "text-mono" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}

function MiniMetric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2">
      <div className="text-[9px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-0.5 text-sm font-bold ${accent ? "text-primary text-mono" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function CompareCard({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: number;
  sub: string;
  tone: "critical" | "secondary";
}) {
  const color = tone === "critical" ? "var(--critical)" : "var(--secondary)";
  return (
    <div
      className="rounded-lg border bg-surface p-4 relative overflow-hidden"
      style={{ borderColor: `color-mix(in oklab, ${color} 40%, transparent)` }}
    >
      <div className="text-[10px] uppercase tracking-wider font-semibold" style={{ color }}>
        {label}
      </div>
      <div className="mt-1 text-4xl font-bold text-mono">{value.toLocaleString()}</div>
      <div className="text-xs text-muted-foreground mt-0.5">{sub}</div>
      <div
        className="absolute inset-x-0 bottom-0 h-1"
        style={{ background: color, opacity: 0.7 }}
      />
    </div>
  );
}

function ArrowFlow() {
  return (
    <div className="relative h-8 w-24">
      <div
        className="absolute inset-y-1/2 left-0 right-3 h-px"
        style={{ background: "var(--gradient-cyber)" }}
      />
      <div
        className="absolute right-0 top-1/2 -translate-y-1/2 h-0 w-0 border-y-[5px] border-y-transparent border-l-[8px]"
        style={{ borderLeftColor: "var(--secondary)" }}
      />
      <div
        className="absolute left-2 top-0 h-1.5 w-1.5 rounded-full animate-pulse"
        style={{ background: "var(--primary)", boxShadow: "0 0 6px var(--primary)" }}
      />
    </div>
  );
}

function ConfidenceRing({ value }: { value: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <svg width="64" height="64" viewBox="0 0 64 64">
      <circle cx="32" cy="32" r={r} fill="none" stroke="var(--accent)" strokeWidth="6" />
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        stroke="url(#cg)"
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={offset}
        transform="rotate(-90 32 32)"
      />
      <defs>
        <linearGradient id="cg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="oklch(0.72 0.19 42)" />
          <stop offset="100%" stopColor="oklch(0.78 0.15 175)" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function EvidenceIcon({ type }: { type: Evidence["type"] }) {
  const map = {
    deploy_correlation: GitBranch,
    ticket_pattern: Activity,
    customer_impact: Users,
    similar_ticket: BrainCircuit,
  } as const;
  const Icon = map[type];
  return (
    <div className="h-7 w-7 rounded-md border border-primary/30 bg-primary/10 flex items-center justify-center text-primary shrink-0">
      <Icon className="h-3.5 w-3.5" />
    </div>
  );
}

type Evidence = import("@/lib/mock-data").Evidence;
