import { cn } from "@/lib/utils";
import { forwardRef, type ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "outline" | "cyber";
  size?: "sm" | "md" | "lg";
}

export const FxButton = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", ...rest }, ref) => {
    const base =
      "inline-flex items-center justify-center gap-2 font-semibold tracking-tight rounded-md transition-all whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50";
    const sizes = {
      sm: "h-8 px-3 text-xs",
      md: "h-10 px-4 text-sm",
      lg: "h-12 px-6 text-sm",
    };
    const variants = {
      primary: "text-primary-foreground hover:brightness-110",
      cyber: "text-primary-foreground hover:brightness-110",
      ghost: "text-foreground hover:bg-accent",
      outline:
        "border border-border bg-surface text-foreground hover:border-primary/40 hover:bg-card",
    };
    const style =
      variant === "primary"
        ? { background: "var(--gradient-primary)", boxShadow: "var(--shadow-glow)" }
        : variant === "cyber"
          ? { background: "var(--gradient-cyber)" }
          : undefined;
    return (
      <button
        ref={ref}
        className={cn(base, sizes[size], variants[variant], className)}
        style={style}
        {...rest}
      />
    );
  },
);
FxButton.displayName = "FxButton";
