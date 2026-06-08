import { createFileRoute, Link } from "@tanstack/react-router";
import { Logo } from "@/components/fixloop/Logo";
import { FxButton } from "@/components/fixloop/Button";
import { Panel } from "@/components/fixloop/Panel";
import { SeverityBadge } from "@/components/fixloop/SeverityBadge";
import { clusters, ticketVolumeTrend } from "@/lib/mock-data";
import {
  ArrowRight, PlayCircle, Search, Layers, GitBranch, Wrench, ShieldCheck,
  AlertOctagon, Sparkles, ChevronRight, Activity, Target, LineChart as LineIcon,
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, Tooltip } from "recharts";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "FixLoop AI — From Customer Pain to Verified Product Fixes" },
      { name: "description", content: "Transform thousands of support tickets into root-cause intelligence, deployment correlations, and verified product fixes." },
      { property: "og:title", content: "FixLoop AI — Product Intelligence Platform" },
      { property: "og:description", content: "From Customer Pain to Verified Product Fixes." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      <SiteHeader />
      <Hero />
      <Problem />
      <HowItWorks />
      <ProductPreview />
      <Advantage />
      <FinalCta />
      <SiteFooter />
    </div>
  );
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center">
        <Logo />
        <nav className="hidden md:flex items-center gap-7 ml-12 text-sm text-muted-foreground">
          <a href="#problem" className="hover:text-foreground">Problem</a>
          <a href="#how" className="hover:text-foreground">How it works</a>
          <a href="#preview" className="hover:text-foreground">Product</a>
          <a href="#advantage" className="hover:text-foreground">Why FixLoop</a>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link to="/dashboard"><FxButton variant="ghost" size="sm">Sign in</FxButton></Link>
          <Link to="/dashboard"><FxButton size="sm">Launch app <ArrowRight className="h-3.5 w-3.5" /></FxButton></Link>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative">
      <div className="absolute inset-0 grid-bg opacity-40" />
      <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at top, color-mix(in oklab, var(--primary) 18%, transparent), transparent 60%)" }} />
      <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-24">
        <div className="grid lg:grid-cols-[1.1fr_1fr] gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 px-3 py-1 text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary" style={{ boxShadow: "0 0 6px var(--secondary)" }} />
              <span className="text-mono">Q2 2026 · Now correlating deploys</span>
            </div>
            <h1 className="mt-6 text-5xl md:text-6xl font-bold leading-[1.05] tracking-tight">
              Your support queue knows what's broken.<br />
              <span className="bg-clip-text text-transparent" style={{ backgroundImage: "var(--gradient-cyber)" }}>FixLoop proves it.</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-xl">
              Transform thousands of support tickets into root-cause intelligence, deployment correlations, and verified product fixes — automatically.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to="/dashboard"><FxButton size="lg">Analyze Tickets <ArrowRight className="h-4 w-4" /></FxButton></Link>
              <FxButton size="lg" variant="outline"><PlayCircle className="h-4 w-4" />Watch Demo</FxButton>
            </div>
            <div className="mt-10 grid grid-cols-3 gap-6 max-w-md">
              <Stat n="12,480" l="Tickets analyzed" />
              <Stat n="$340K" l="Risk surfaced" />
              <Stat n="91%" l="Deflection rate" />
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-4 rounded-2xl" style={{ background: "var(--gradient-cyber)", filter: "blur(60px)", opacity: 0.2 }} />
            <div className="relative rounded-xl border border-border bg-card shadow-2xl overflow-hidden">
              <div className="flex items-center gap-1.5 px-3 py-2 border-b border-border bg-surface">
                <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--critical)]" />
                <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--warning)]" />
                <span className="h-2.5 w-2.5 rounded-full bg-secondary" />
                <span className="ml-3 text-[11px] text-mono text-muted-foreground">fixloop.ai / clusters</span>
              </div>
              <div className="p-5 space-y-3">
                {clusters.slice(0, 3).map((c) => (
                  <div key={c.id} className="rounded-lg border border-border bg-surface p-3">
                    <div className="flex items-center justify-between">
                      <div className="text-[10px] text-mono text-muted-foreground uppercase tracking-wider">{c.id}</div>
                      <SeverityBadge severity={c.severity} />
                    </div>
                    <div className="mt-1.5 text-sm font-semibold leading-tight">{c.title}</div>
                    <div className="mt-2 flex items-center gap-4 text-[11px] text-mono text-muted-foreground">
                      <span>{c.ticketCount} tickets</span>
                      <span className="text-primary">${(c.monthlyCost/1000).toFixed(1)}k/mo</span>
                      <span className="ml-auto text-secondary">{c.confidence}% confidence</span>
                    </div>
                  </div>
                ))}
                <div className="h-24 rounded-lg border border-border bg-surface px-3 pt-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Ticket volume · 7d</div>
                  <ResponsiveContainer width="100%" height={60}>
                    <AreaChart data={ticketVolumeTrend}>
                      <defs>
                        <linearGradient id="hero-g" x1="0" x2="0" y1="0" y2="1">
                          <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.6} />
                          <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="day" hide />
                      <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", fontSize: 11, borderRadius: 6 }} />
                      <Area type="monotone" dataKey="tickets" stroke="var(--primary)" strokeWidth={1.5} fill="url(#hero-g)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Stat({ n, l }: { n: string; l: string }) {
  return (
    <div>
      <div className="text-2xl font-bold text-mono">{n}</div>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{l}</div>
    </div>
  );
}

function Problem() {
  const items = [
    { icon: AlertOctagon, title: "Tickets pile up in silos", body: "Support, success, and engineering each see fragments. Nobody sees the pattern." },
    { icon: Activity, title: "Root cause is guesswork", body: "By the time a trend is obvious, customers have already churned." },
    { icon: GitBranch, title: "Deploys go uncorrelated", body: "Releases ship without ever knowing which ones caused the next wave of complaints." },
  ];
  return (
    <section id="problem" className="relative border-y border-border bg-surface/50">
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="max-w-3xl">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">The Problem</div>
          <h2 className="mt-2 text-4xl font-bold tracking-tight">Companies treat tickets as support data. FixLoop treats them as product intelligence.</h2>
        </div>
        <div className="mt-12 grid md:grid-cols-3 gap-5">
          {items.map((it) => (
            <div key={it.title} className="rounded-lg border border-border bg-card p-6">
              <div className="h-10 w-10 rounded-md border border-border flex items-center justify-center" style={{ background: "color-mix(in oklab, var(--critical) 14%, transparent)" }}>
                <it.icon className="h-5 w-5 text-[color:var(--critical)]" />
              </div>
              <div className="mt-4 font-semibold">{it.title}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{it.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { icon: Search, title: "Ingest", body: "Connect Zendesk, Intercom, Linear, GitHub, and your release feed. FixLoop normalizes every signal." },
    { icon: Layers, title: "Cluster", body: "AI groups thousands of tickets into root-cause clusters with confidence scores and business impact." },
    { icon: GitBranch, title: "Correlate", body: "Every deploy is time-aligned with downstream pain. See causal links you'd never find by hand." },
    { icon: Wrench, title: "Resolve", body: "Recommended fixes, owners, and expected deflection. Closed loops with verified before/after." },
  ];
  return (
    <section id="how" className="relative">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <div className="max-w-3xl">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">How it works</div>
          <h2 className="mt-2 text-4xl font-bold tracking-tight">Four steps from raw tickets to verified fixes.</h2>
        </div>
        <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((s, i) => (
            <div key={s.title} className="relative rounded-lg border border-border bg-card p-6 group hover:border-primary/40 transition-colors">
              <div className="absolute top-4 right-4 text-[11px] text-mono text-muted-foreground">0{i+1}</div>
              <div className="h-10 w-10 rounded-md flex items-center justify-center" style={{ background: "var(--gradient-cyber)" }}>
                <s.icon className="h-5 w-5 text-primary-foreground" />
              </div>
              <div className="mt-4 font-semibold">{s.title}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{s.body}</p>
              {i < steps.length - 1 && <ChevronRight className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-border" />}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ProductPreview() {
  return (
    <section id="preview" className="relative border-y border-border bg-surface/50">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <div className="max-w-3xl">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">Product</div>
          <h2 className="mt-2 text-4xl font-bold tracking-tight">An intelligence ops center, not a support inbox.</h2>
          <p className="mt-3 text-muted-foreground">High-information density. Built for product, engineering, and execs to see the same truth.</p>
        </div>

        <div className="mt-12 grid lg:grid-cols-3 gap-4">
          <FeatureCard icon={Layers} title="Cluster Explorer" body="Auto-discovered groups with severity, customer count, monthly cost, and confidence." to="/clusters" />
          <FeatureCard icon={Activity} title="Causal Timeline" body="Deploys, releases, and clusters on one timeline. Correlation lines tell the story." to="/timeline" />
          <FeatureCard icon={Wrench} title="Resolution Center" body="Recommended fixes with expected deflection, owners, and verified before/after." to="/resolution" />
          <FeatureCard icon={LineIcon} title="Health Dashboard" body="Revenue at risk, open clusters, customers affected, deflection rate — live." to="/dashboard" />
          <FeatureCard icon={Target} title="Priority Ranking" body="What to fix next, ranked by combined volume, severity, and revenue impact." to="/report" />
          <FeatureCard icon={Sparkles} title="Executive Briefs" body="Board-ready PDF reports generated from real ticket data, not hand-rolled slides." to="/report" />
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ icon: Icon, title, body, to }: any) {
  return (
    <Link to={to} className="group rounded-lg border border-border bg-card p-6 hover:border-primary/40 transition-colors block">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-md border border-border flex items-center justify-center" style={{ background: "color-mix(in oklab, var(--primary) 12%, transparent)" }}>
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div className="font-semibold">{title}</div>
        <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
      </div>
      <p className="mt-3 text-sm text-muted-foreground">{body}</p>
    </Link>
  );
}

function Advantage() {
  const rows = [
    ["Treats tickets as", "Support workload", "Product intelligence"],
    ["Root cause discovery", "Manual triage", "AI-clustered, scored, ranked"],
    ["Deploy correlation", "None", "Time-aligned, confidence-weighted"],
    ["Business impact", "Ticket counts", "Revenue at risk + recovered"],
    ["Verification", "Anecdotal", "Measured before/after deflection"],
  ];
  return (
    <section id="advantage" className="relative">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <div className="max-w-3xl">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">Competitive advantage</div>
          <h2 className="mt-2 text-4xl font-bold tracking-tight">A help desk gives you tickets. FixLoop closes the loop.</h2>
        </div>

        <div className="mt-10 rounded-lg border border-border bg-card overflow-hidden">
          <div className="grid grid-cols-[1.4fr_1fr_1fr] text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
            <div className="px-5 py-3 font-semibold">Dimension</div>
            <div className="px-5 py-3 font-semibold">Legacy help desk</div>
            <div className="px-5 py-3 font-semibold text-primary">FixLoop AI</div>
          </div>
          {rows.map((r, i) => (
            <div key={i} className="grid grid-cols-[1.4fr_1fr_1fr] border-b border-border/50 last:border-0 text-sm">
              <div className="px-5 py-3 font-medium">{r[0]}</div>
              <div className="px-5 py-3 text-muted-foreground">{r[1]}</div>
              <div className="px-5 py-3 text-foreground flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-secondary" />{r[2]}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="relative">
      <div className="max-w-7xl mx-auto px-6 pb-24">
        <div className="relative overflow-hidden rounded-2xl border border-border p-12 text-center">
          <div className="absolute inset-0 grid-bg opacity-40" />
          <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at center, color-mix(in oklab, var(--primary) 22%, transparent), transparent 70%)" }} />
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight max-w-3xl mx-auto">Close the loop on every complaint, every deploy, every dollar at risk.</h2>
            <p className="mt-4 text-muted-foreground max-w-xl mx-auto">Spin up FixLoop on your ticket history in under an hour. See the first cluster within minutes.</p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link to="/dashboard"><FxButton size="lg">Analyze Tickets <ArrowRight className="h-4 w-4" /></FxButton></Link>
              <FxButton size="lg" variant="outline"><PlayCircle className="h-4 w-4" />Watch Demo</FxButton>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-border bg-surface/40">
      <div className="max-w-7xl mx-auto px-6 py-10 flex flex-wrap items-center gap-4">
        <Logo />
        <span className="text-xs text-muted-foreground text-mono">© 2026 FixLoop AI · Product Intelligence Platform</span>
        <div className="ml-auto flex items-center gap-5 text-xs text-muted-foreground">
          <a href="#" className="hover:text-foreground">Security</a>
          <a href="#" className="hover:text-foreground">Docs</a>
          <a href="#" className="hover:text-foreground">Status</a>
        </div>
      </div>
    </footer>
  );
}
