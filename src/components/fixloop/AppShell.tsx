import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Boxes,
  Activity,
  Wrench,
  FileBarChart2,
  Search,
  Bell,
  ChevronDown,
  BrainCircuit,
  User,
  Settings as SettingsIcon,
} from "lucide-react";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/clusters", label: "Clusters", icon: Boxes },
  { to: "/timeline", label: "Timeline", icon: Activity },
  { to: "/ai-command-center", label: "AI Command Center", icon: BrainCircuit },
  { to: "/resolution", label: "Resolution Center", icon: Wrench },
  { to: "/report", label: "Reports", icon: FileBarChart2 },
] as const;

const workspaceNav = [
  { to: "/profile", label: "Profile", icon: User },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
] as const;

export function AppShell() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      <aside className="w-60 shrink-0 border-r border-border bg-sidebar flex flex-col sticky top-0 h-screen">
        <div className="h-14 px-4 flex items-center border-b border-sidebar-border">
          <Link to="/">
            <Logo />
          </Link>
        </div>
        <div className="px-3 py-3 border-b border-sidebar-border">
          <div className="flex items-center justify-between rounded-md border border-sidebar-border bg-sidebar-accent/40 px-2.5 py-1.5">
            <div className="flex items-center gap-2 min-w-0">
              <div
                className="h-5 w-5 rounded-sm flex items-center justify-center text-[10px] font-bold text-mono"
                style={{ background: "var(--gradient-cyber)", color: "var(--primary-foreground)" }}
              >
                A
              </div>
              <div className="text-xs font-medium truncate">Acme Corp</div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          <div className="px-2.5 pb-1.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Intelligence
          </div>
          {nav.map((item) => {
            const active =
              pathname === item.to || (item.to !== "/dashboard" && pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                )}
              >
                <item.icon className={cn("h-4 w-4", active && "text-primary")} />
                <span>{item.label}</span>
                {active && (
                  <span
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-primary"
                    style={{ boxShadow: "0 0 6px var(--primary)" }}
                  />
                )}
              </Link>
            );
          })}
          <div className="px-2.5 pt-4 pb-1.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Workspace
          </div>
          {workspaceNav.map((item) => {
            const active = pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                )}
              >
                <item.icon className={cn("h-4 w-4", active && "text-primary")} />
                <span>{item.label}</span>
                {active && (
                  <span
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-primary"
                    style={{ boxShadow: "0 0 6px var(--primary)" }}
                  />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-sidebar-border p-3">
          <div className="rounded-md border border-sidebar-border bg-sidebar-accent/30 p-3">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
              <span
                className="h-1.5 w-1.5 rounded-full bg-secondary"
                style={{ boxShadow: "0 0 6px var(--secondary)" }}
              />
              Live ingestion
            </div>
            <div className="mt-1 text-xs text-mono">12,480 tickets · 6 sources</div>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-20 h-14 border-b border-border bg-background/80 backdrop-blur-md flex items-center px-6 gap-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground text-mono">
            <span>Workspace</span>
            <span>/</span>
            <span className="text-foreground">{currentLabel(pathname)}</span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden md:flex items-center gap-2 h-8 px-2.5 rounded-md border border-border bg-surface w-72">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                placeholder="Search clusters, deploys, tickets…"
                className="bg-transparent flex-1 text-xs outline-none placeholder:text-muted-foreground"
              />
              <kbd className="text-[10px] text-mono text-muted-foreground border border-border rounded px-1">
                ⌘K
              </kbd>
            </div>
            <button className="h-8 w-8 rounded-md border border-border bg-surface flex items-center justify-center relative hover:border-primary/40">
              <Bell className="h-3.5 w-3.5" />
              <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
            </button>
            <div
              className="h-8 w-8 rounded-md text-[11px] font-bold flex items-center justify-center text-mono"
              style={{ background: "var(--gradient-cyber)", color: "var(--primary-foreground)" }}
            >
              NK
            </div>
          </div>
        </header>
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function currentLabel(p: string) {
  if (p.startsWith("/dashboard")) return "Dashboard";
  if (p.startsWith("/clusters")) return "Cluster Explorer";
  if (p.startsWith("/timeline")) return "Causal Timeline";
  if (p.startsWith("/ai-command-center")) return "AI Command Center";
  if (p.startsWith("/resolution")) return "Resolution Center";
  if (p.startsWith("/report")) return "Executive Report";
  if (p.startsWith("/profile")) return "Profile";
  if (p.startsWith("/settings")) return "Settings";
  return "Workspace";
}
