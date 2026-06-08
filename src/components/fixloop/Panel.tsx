import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-border bg-card overflow-hidden", className)}>
      {(title || action) && (
        <div className="flex items-start justify-between border-b border-border px-5 py-3.5">
          <div>
            {title && <div className="text-sm font-semibold tracking-tight">{title}</div>}
            {subtitle && <div className="text-xs text-muted-foreground mt-0.5">{subtitle}</div>}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
