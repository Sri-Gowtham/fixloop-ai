import { cn } from "@/lib/utils";

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative h-7 w-7">
        <div
          className="absolute inset-0 rounded-md"
          style={{ background: "var(--gradient-cyber)" }}
        />
        <div className="absolute inset-[3px] rounded-[5px] bg-background flex items-center justify-center">
          <div
            className="h-2 w-2 rounded-full"
            style={{ background: "var(--primary)", boxShadow: "0 0 8px var(--primary)" }}
          />
        </div>
      </div>
      {!compact && (
        <div className="leading-none">
          <div className="text-[15px] font-bold tracking-tight">
            FixLoop<span className="text-primary">.AI</span>
          </div>
          <div className="text-[9px] uppercase tracking-[0.18em] text-muted-foreground mt-0.5">
            Product Intel
          </div>
        </div>
      )}
    </div>
  );
}
