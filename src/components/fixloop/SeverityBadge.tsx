import { cn } from "@/lib/utils";
import type { Severity, Status } from "@/lib/mock-data";

const sevMap: Record<Severity, { label: string; cls: string }> = {
  critical: {
    label: "Critical",
    cls: "text-[color:var(--critical)] bg-[color:var(--critical)]/10 border-[color:var(--critical)]/30",
  },
  high: { label: "High", cls: "text-primary bg-primary/10 border-primary/30" },
  medium: {
    label: "Medium",
    cls: "text-[color:var(--warning)] bg-[color:var(--warning)]/10 border-[color:var(--warning)]/30",
  },
  low: { label: "Low", cls: "text-secondary bg-secondary/10 border-secondary/30" },
};

const statusMap: Record<Status, { label: string; cls: string }> = {
  open: {
    label: "Open",
    cls: "text-[color:var(--critical)] bg-[color:var(--critical)]/10 border-[color:var(--critical)]/30",
  },
  in_progress: {
    label: "In Progress",
    cls: "text-[color:var(--warning)] bg-[color:var(--warning)]/10 border-[color:var(--warning)]/30",
  },
  resolved: { label: "Resolved", cls: "text-secondary bg-secondary/10 border-secondary/30" },
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const s = sevMap[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        s.cls,
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {s.label}
    </span>
  );
}

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const s = statusMap[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        s.cls,
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {s.label}
    </span>
  );
}
