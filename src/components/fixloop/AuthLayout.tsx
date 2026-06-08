import { type ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { Logo } from "./Logo";
import { ShieldCheck, BrainCircuit, Activity } from "lucide-react";

export function AuthLayout({ eyebrow, title, subtitle, children, footer }: { eyebrow: string; title: string; subtitle: string; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-background text-foreground">
      {/* Left brand panel */}
      <div className="hidden lg:flex relative overflow-hidden border-r border-border" style={{ background: "var(--gradient-surface)" }}>
        <div className="absolute inset-0 grid-bg opacity-60" />
        <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full" style={{ background: "radial-gradient(circle, oklch(0.72 0.19 42 / 0.25), transparent 70%)" }} />
        <div className="absolute -bottom-40 -right-20 h-[28rem] w-[28rem] rounded-full" style={{ background: "radial-gradient(circle, oklch(0.78 0.15 175 / 0.18), transparent 70%)" }} />
        <div className="relative z-10 flex flex-col p-10 w-full">
          <Link to="/"><Logo /></Link>
          <div className="mt-auto space-y-6 max-w-md">
            <div className="inline-flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary text-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" style={{ boxShadow: "0 0 6px var(--primary)" }} />
              Product Intelligence · v3
            </div>
            <h2 className="text-3xl font-bold tracking-tight leading-tight">From customer pain to <span className="text-primary">verified product fixes.</span></h2>
            <p className="text-sm text-muted-foreground">FixLoop AI turns every ticket into root-cause intelligence, deploy correlations, and revenue-recovering fixes — autonomously.</p>
            <div className="space-y-2.5">
              {[
                { icon: Activity, label: "Continuous root-cause clustering across 6+ sources" },
                { icon: BrainCircuit, label: "Explainable AI investigations with confidence scores" },
                { icon: ShieldCheck, label: "Loop closure validation — measure deflection, not deploys" },
              ].map((f, i) => (
                <div key={i} className="flex items-center gap-3 rounded-md border border-border bg-card/60 backdrop-blur px-3 py-2">
                  <div className="h-7 w-7 rounded-md flex items-center justify-center text-primary-foreground" style={{ background: "var(--gradient-cyber)" }}>
                    <f.icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="text-xs text-foreground">{f.label}</div>
                </div>
              ))}
            </div>
            <div className="pt-4 border-t border-border text-[10px] text-mono uppercase tracking-wider text-muted-foreground">
              Trusted by product teams at Acme · Northwind · Globex · Initech
            </div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-col">
        <div className="lg:hidden flex items-center justify-between p-6 border-b border-border">
          <Link to="/"><Logo /></Link>
        </div>
        <div className="flex-1 flex items-center justify-center p-6 lg:p-10">
          <div className="w-full max-w-md">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">{eyebrow}</div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight">{title}</h1>
            <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
            <div className="mt-7">{children}</div>
            {footer && <div className="mt-6 text-sm text-muted-foreground">{footer}</div>}
          </div>
        </div>
        <div className="px-6 lg:px-10 py-5 border-t border-border flex items-center justify-between text-[10px] text-mono uppercase tracking-wider text-muted-foreground">
          <span>© 2026 FixLoop AI</span>
          <span className="flex items-center gap-3">
            <span>SOC 2 Type II</span>
            <span>·</span>
            <span>GDPR</span>
          </span>
        </div>
      </div>
    </div>
  );
}

export function AuthInput({ label, type = "text", placeholder, autoComplete }: { label: string; type?: string; placeholder?: string; autoComplete?: string }) {
  return (
    <label className="block">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">{label}</div>
      <input type={type} placeholder={placeholder} autoComplete={autoComplete} className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20" />
    </label>
  );
}

export function SsoButton({ provider, children }: { provider: "google" | "microsoft"; children: React.ReactNode }) {
  return (
    <button className="h-11 w-full rounded-md border border-border bg-surface hover:border-primary/40 hover:bg-card transition-colors flex items-center justify-center gap-2.5 text-sm font-semibold">
      {provider === "google" ? <GoogleMark /> : <MicrosoftMark />}
      {children}
    </button>
  );
}

function GoogleMark() {
  return (
    <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.6 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.5 6.5 29.5 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5c11 0 19.5-8 19.5-19.5 0-1.2-.1-2.3-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 18.9 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7C34.5 6.5 29.5 4.5 24 4.5 16.3 4.5 9.6 8.9 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 43.5c5.4 0 10.3-2 14-5.3l-6.5-5.3c-2 1.4-4.6 2.2-7.5 2.2-5.3 0-9.8-3.4-11.4-8.1l-6.6 5.1C9.5 39 16.2 43.5 24 43.5z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.3 5.6l6.5 5.3C41.8 35.4 43.5 30 43.5 24c0-1.2-.1-2.3-.4-3.5z" />
    </svg>
  );
}

function MicrosoftMark() {
  return (
    <svg width="14" height="14" viewBox="0 0 23 23" aria-hidden>
      <rect width="10" height="10" x="1" y="1" fill="#F25022" />
      <rect width="10" height="10" x="12" y="1" fill="#7FBA00" />
      <rect width="10" height="10" x="1" y="12" fill="#00A4EF" />
      <rect width="10" height="10" x="12" y="12" fill="#FFB900" />
    </svg>
  );
}