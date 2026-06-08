import { Link } from "@tanstack/react-router";
import { type Cluster } from "@/lib/mock-data";
import { SeverityBadge } from "./SeverityBadge";
import { ArrowUpRight, Users, DollarSign, Sparkles } from "lucide-react";

export function ClusterCard({ cluster }: { cluster: Cluster }) {
  return (
    <Link
      to="/clusters"
      className="group relative block overflow-hidden rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/40 hover:bg-card/80"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] text-mono text-muted-foreground uppercase tracking-wider">
            <span>{cluster.id}</span>
            <span>·</span>
            <span>{cluster.ticketCount} tickets</span>
          </div>
          <h3 className="mt-1.5 text-base font-semibold leading-tight tracking-tight">
            {cluster.title}
          </h3>
          <p className="mt-1.5 text-sm text-muted-foreground line-clamp-2">{cluster.summary}</p>
        </div>
        <SeverityBadge severity={cluster.severity} />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-border pt-4">
        <Stat
          icon={DollarSign}
          label="Monthly cost"
          value={`$${(cluster.monthlyCost / 1000).toFixed(1)}k`}
        />
        <Stat icon={Users} label="Customers" value={cluster.affectedCustomers.toString()} />
        <Stat icon={Sparkles} label="Confidence" value={`${cluster.confidence}%`} />
      </div>

      <div className="mt-3 flex items-center justify-between text-xs">
        <span className="text-muted-foreground text-mono">
          {cluster.relatedDeploy ? `Linked to ${cluster.relatedDeploy}` : "No deploy correlation"}
        </span>
        <span className="inline-flex items-center gap-1 text-primary opacity-0 transition-opacity group-hover:opacity-100">
          Inspect <ArrowUpRight className="h-3 w-3" />
        </span>
      </div>
    </Link>
  );
}

function Stat({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-muted-foreground">
        <Icon className="h-2.5 w-2.5" />
        {label}
      </div>
      <div className="text-sm font-semibold text-mono mt-0.5">{value}</div>
    </div>
  );
}
