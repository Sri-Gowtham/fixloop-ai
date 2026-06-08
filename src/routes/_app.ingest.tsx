import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/fixloop/PageHeader";
import { Panel } from "@/components/fixloop/Panel";
import { FxButton } from "@/components/fixloop/Button";
import {
  Upload,
  FileSpreadsheet,
  LifeBuoy,
  FileText,
  CheckCircle2,
  Loader2,
  Database,
  Brain,
  Network,
  GitCommit,
  Wrench,
  DollarSign,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/ingest")({
  head: () => ({ meta: [{ title: "Ingest · FixLoop AI" }] }),
  component: IngestPage,
});

const STAGES = [
  {
    key: "ingest",
    label: "Tickets Ingested",
    icon: Database,
    detail: "Parsing rows, normalizing fields",
  },
  {
    key: "cluster",
    label: "AI Clustering",
    icon: Brain,
    detail: "Embedding + density-based grouping",
  },
  {
    key: "root",
    label: "Root Cause Detection",
    icon: Network,
    detail: "Mining causal signals across tickets",
  },
  {
    key: "deploy",
    label: "Deploy Correlation",
    icon: GitCommit,
    detail: "Linking spikes to release events",
  },
  {
    key: "fix",
    label: "Fix Recommendation",
    icon: Wrench,
    detail: "Synthesizing actionable patches",
  },
  {
    key: "impact",
    label: "Impact Calculation",
    icon: DollarSign,
    detail: "Quantifying revenue at risk",
  },
] as const;

type Source = { id: string; label: string; sub: string; icon: typeof FileSpreadsheet };
const SOURCES: Source[] = [
  { id: "csv", label: "CSV", sub: "Generic tabular export", icon: FileSpreadsheet },
  { id: "zendesk", label: "Zendesk Export", sub: "tickets.json or .zip", icon: LifeBuoy },
  { id: "logs", label: "Support Logs", sub: ".log / .ndjson stream", icon: FileText },
];

function IngestPage() {
  const [source, setSource] = useState<string>("zendesk");
  const [fileName, setFileName] = useState<string>("acme_q2_tickets.json");
  const [fileSize, setFileSize] = useState<string>("18.4 MB");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [stageIdx, setStageIdx] = useState(-1);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!running) return;
    if (stageIdx >= STAGES.length) {
      setRunning(false);
      setDone(true);
      return;
    }
    const dur = 1400;
    const start = Date.now();
    const id = setInterval(() => {
      const p = Math.min(1, (Date.now() - start) / dur);
      setProgress(p);
      if (p >= 1) {
        clearInterval(id);
        setStageIdx((s) => s + 1);
        setProgress(0);
      }
    }, 40);
    return () => clearInterval(id);
  }, [running, stageIdx]);

  const start = () => {
    setDone(false);
    setStageIdx(0);
    setProgress(0);
    setRunning(true);
  };
  const reset = () => {
    setRunning(false);
    setDone(false);
    setStageIdx(-1);
    setProgress(0);
  };

  const onFile = (f?: File) => {
    if (!f) return;
    setFileName(f.name);
    setFileSize(`${(f.size / (1024 * 1024)).toFixed(1)} MB`);
  };

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        eyebrow="Pipeline"
        title="Ingest & Analyze"
        description="Stream support data into the FixLoop intelligence pipeline. Tickets become clusters, clusters become root causes, root causes become verified fixes."
        actions={
          done ? (
            <Link to="/dashboard">
              <FxButton size="sm">
                Go to Dashboard <ArrowRight className="h-3.5 w-3.5" />
              </FxButton>
            </Link>
          ) : running ? (
            <FxButton size="sm" variant="outline" onClick={reset}>
              Cancel
            </FxButton>
          ) : (
            <FxButton size="sm" onClick={start}>
              <Sparkles className="h-3.5 w-3.5" /> Run analysis
            </FxButton>
          )
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-4">
        <Panel title="Data Source" subtitle="Select the source format and upload a file">
          <div className="grid grid-cols-3 gap-2 mb-4">
            {SOURCES.map((s) => {
              const active = source === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => setSource(s.id)}
                  className={cn(
                    "rounded-md border p-3 text-left transition-all",
                    active
                      ? "border-primary/60 bg-primary/5"
                      : "border-border bg-surface hover:border-primary/30",
                  )}
                >
                  <s.icon
                    className={cn(
                      "h-4 w-4 mb-2",
                      active ? "text-primary" : "text-muted-foreground",
                    )}
                  />
                  <div className="text-xs font-semibold">{s.label}</div>
                  <div className="text-[10px] text-muted-foreground text-mono mt-0.5">{s.sub}</div>
                </button>
              );
            })}
          </div>

          <label className="block border border-dashed border-border rounded-md bg-surface hover:border-primary/40 transition-colors p-6 text-center cursor-pointer">
            <input type="file" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
            <div
              className="h-10 w-10 mx-auto rounded-md flex items-center justify-center"
              style={{ background: "var(--gradient-cyber)" }}
            >
              <Upload className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="mt-3 text-sm font-semibold">Drop file or click to browse</div>
            <div className="text-[11px] text-muted-foreground text-mono mt-1">
              Max 200MB · CSV / JSON / NDJSON / ZIP
            </div>
          </label>

          <div className="mt-3 flex items-center justify-between rounded-md border border-border bg-surface px-3 py-2 text-xs">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="h-3.5 w-3.5 text-secondary shrink-0" />
              <span className="truncate text-mono">{fileName}</span>
            </div>
            <span className="text-mono text-muted-foreground">{fileSize}</span>
          </div>
        </Panel>

        <Panel
          title="Live Status"
          subtitle={
            running ? "Pipeline executing" : done ? "Analysis complete" : "Idle — awaiting run"
          }
        >
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "h-12 w-12 rounded-md flex items-center justify-center border",
                done
                  ? "border-secondary/40 bg-secondary/10"
                  : running
                    ? "border-primary/40 bg-primary/10"
                    : "border-border bg-surface",
              )}
            >
              {done ? (
                <CheckCircle2 className="h-5 w-5 text-secondary" />
              ) : running ? (
                <Loader2 className="h-5 w-5 text-primary animate-spin" />
              ) : (
                <Database className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold truncate">
                {done
                  ? "Verified product intelligence ready"
                  : running
                    ? STAGES[Math.min(stageIdx, STAGES.length - 1)]?.label
                    : "Ready to ingest"}
              </div>
              <div className="text-[11px] text-muted-foreground text-mono mt-0.5">
                {done
                  ? "12,480 tickets · 6 sources · 4 critical clusters"
                  : running
                    ? STAGES[Math.min(stageIdx, STAGES.length - 1)]?.detail
                    : "Configure source and press Run analysis"}
              </div>
            </div>
          </div>

          <div className="mt-4 h-1.5 rounded-full bg-surface overflow-hidden border border-border">
            <div
              className="h-full transition-all duration-100"
              style={{
                width: `${done ? 100 : running ? ((stageIdx + progress) / STAGES.length) * 100 : 0}%`,
                background: "var(--gradient-cyber)",
              }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[10px] text-mono text-muted-foreground uppercase tracking-wider">
            <span>
              Stage {done ? STAGES.length : Math.max(0, stageIdx + 1)} / {STAGES.length}
            </span>
            <span>
              {done
                ? "100"
                : running
                  ? Math.round(((stageIdx + progress) / STAGES.length) * 100)
                  : 0}
              %
            </span>
          </div>
        </Panel>
      </div>

      <Panel
        title="Analysis Pipeline"
        subtitle="Each stage transforms raw signal into product intelligence"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-3">
          {STAGES.map((s, i) => {
            const isDone = done || i < stageIdx;
            const isActive = running && i === stageIdx;
            return (
              <div
                key={s.key}
                className={cn(
                  "relative rounded-md border p-3 transition-all",
                  isDone
                    ? "border-secondary/40 bg-secondary/5"
                    : isActive
                      ? "border-primary/60 bg-primary/5"
                      : "border-border bg-surface",
                )}
                style={isActive ? { boxShadow: "var(--shadow-glow)" } : undefined}
              >
                <div className="flex items-center justify-between">
                  <div
                    className={cn(
                      "h-7 w-7 rounded-md flex items-center justify-center border",
                      isDone
                        ? "border-secondary/40 bg-secondary/10"
                        : isActive
                          ? "border-primary/40 bg-primary/10"
                          : "border-border bg-card",
                    )}
                  >
                    {isDone ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-secondary" />
                    ) : isActive ? (
                      <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
                    ) : (
                      <s.icon className="h-3.5 w-3.5 text-muted-foreground" />
                    )}
                  </div>
                  <span className="text-[9px] text-mono uppercase tracking-wider text-muted-foreground">
                    0{i + 1}
                  </span>
                </div>
                <div className="mt-2.5 text-xs font-semibold leading-tight">{s.label}</div>
                <div className="mt-1 text-[10px] text-muted-foreground leading-snug">
                  {s.detail}
                </div>
                {isActive && (
                  <div className="mt-2 h-0.5 rounded-full bg-surface overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${progress * 100}%` }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-5 rounded-md border border-border bg-surface/60 p-3 text-[11px] text-mono text-muted-foreground max-h-40 overflow-y-auto space-y-1">
          <LogLine done={done || stageIdx > 0} active={stageIdx === 0 && running}>
            ingest · parsed 12,480 rows · 6 channels
          </LogLine>
          <LogLine done={done || stageIdx > 1} active={stageIdx === 1 && running}>
            cluster · embedded 12,480 tickets · 38 clusters formed
          </LogLine>
          <LogLine done={done || stageIdx > 2} active={stageIdx === 2 && running}>
            root-cause · 4 critical · 7 high-severity hypotheses
          </LogLine>
          <LogLine done={done || stageIdx > 3} active={stageIdx === 3 && running}>
            deploy-link · matched 11 release events (p &lt; 0.01)
          </LogLine>
          <LogLine done={done || stageIdx > 4} active={stageIdx === 4 && running}>
            fix-rec · 9 recommendations synthesized
          </LogLine>
          <LogLine done={done || stageIdx > 5} active={stageIdx === 5 && running}>
            impact · revenue-at-risk computed: $284,300 / mo
          </LogLine>
        </div>
      </Panel>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <ResultCard label="Tickets analyzed" value="12,480" sub="across 6 sources" />
        <ResultCard label="Clusters found" value="38" sub="4 critical · 7 high" tone="primary" />
        <ResultCard label="Revenue risk" value="$284.3k" sub="monthly at risk" tone="critical" />
        <ResultCard label="Critical issues" value="4" sub="awaiting fix" tone="warning" />
      </div>

      {done && (
        <div
          className="rounded-lg border border-primary/40 bg-primary/5 p-5 flex flex-wrap items-center justify-between gap-4 animate-fade-in"
          style={{ boxShadow: "var(--shadow-glow)" }}
        >
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
              Pipeline complete
            </div>
            <div className="mt-1 text-base font-bold">Intelligence ready for review</div>
            <div className="text-xs text-muted-foreground mt-0.5">
              Inspect clusters, validate root causes, and ship verified fixes.
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/clusters">
              <FxButton size="sm" variant="outline">
                View clusters
              </FxButton>
            </Link>
            <Link to="/dashboard">
              <FxButton size="sm">
                Go to Dashboard <ArrowRight className="h-3.5 w-3.5" />
              </FxButton>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function LogLine({
  done,
  active,
  children,
}: {
  done: boolean;
  active: boolean;
  children: React.ReactNode;
}) {
  if (!done && !active) return <div className="opacity-30">› {children}</div>;
  return (
    <div className={cn("flex items-start gap-2", active && "text-foreground")}>
      <span className={cn(active ? "text-primary" : "text-secondary")}>{active ? "▸" : "✓"}</span>
      <span>{children}</span>
    </div>
  );
}

function ResultCard({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  tone?: "primary" | "critical" | "warning";
}) {
  const color =
    tone === "primary"
      ? "text-primary"
      : tone === "critical"
        ? "text-[color:var(--critical)]"
        : tone === "warning"
          ? "text-[color:var(--warning)]"
          : "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground text-mono">
        {label}
      </div>
      <div className={cn("mt-2 text-2xl font-bold text-mono", color)}>{value}</div>
      <div className="mt-1 text-[11px] text-muted-foreground">{sub}</div>
    </div>
  );
}
