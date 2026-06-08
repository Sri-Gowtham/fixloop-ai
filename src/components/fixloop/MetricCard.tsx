import { cn } from "@/lib/utils";
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string;
  delta?: string;
  deltaDir?: "up" | "down";
  deltaGood?: "up" | "down";
  icon?: LucideIcon;
  accent?: "primary" | "secondary" | "warning" | "critical";
  spark?: number[];
}

export function MetricCard({ label, value, delta, deltaDir, deltaGood = "up", icon: Icon, accent = "primary", spark }: Props) {
  const accentColor = {
    primary: "var(--primary)",
    secondary: "var(--secondary)",
    warning: "var(--warning)",
    critical: "var(--critical)",
  }[accent];

  const good = deltaDir === deltaGood;

  return (
    <div className="group relative overflow-hidden rounded-lg border border-border bg-card p-5 transition-colors hover:border-border/80">
      <div className="absolute inset-x-0 top-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }} />
      <div className="flex items-start justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
        {Icon && (
          <div className="h-8 w-8 rounded-md flex items-center justify-center border border-border" style={{ background: `color-mix(in oklab, ${accentColor} 12%, transparent)` }}>
            <Icon className="h-4 w-4" style={{ color: accentColor }} />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <div className="text-3xl font-bold tracking-tight text-mono">{value}</div>
        {delta && (
          <div className={cn("inline-flex items-center gap-0.5 text-xs font-semibold", good ? "text-secondary" : "text-[color:var(--critical)]")}>
            {deltaDir === "up" ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {delta}
          </div>
        )}
      </div>
      {spark && <Sparkline data={spark} color={accentColor} />}
    </div>
  );
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 100, h = 28;
  const step = w / (data.length - 1);
  const points = data.map((v, i) => `${i * step},${h - ((v - min) / range) * h}`).join(" ");
  const id = `spk-${Math.random().toString(36).slice(2, 8)}`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 h-7 w-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.5" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
      <polygon points={`0,${h} ${points} ${w},${h}`} fill={`url(#${id})`} />
    </svg>
  );
}