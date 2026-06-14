import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export interface DeploymentRow {
  id: string;
  version: string;
  title: string;
  date: string; // mapped from deployed_at
  notes?: string;
  risk: "critical" | "high" | "medium" | "low";
}

interface DeploymentApiRow {
  id: string;
  version: string;
  title?: string;
  deployed_at?: string;
  notes?: string;
  risk?: string;
}

export function useDeployments(start?: string, end?: string) {
  return useQuery({
    queryKey: queryKeys.timeline.deployments({ start, end } as any),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (start) params.start = start;
      if (end) params.end = end;

      const { data } = await api.get<DeploymentApiRow[]>("/ai/deployments", { params });

      return (data || []).map((d) => ({
        id: d.id,
        version: d.version || d.id,
        title: d.title || "",
        date: d.deployed_at ? new Date(d.deployed_at).toISOString().split("T")[0] : "",
        notes: d.notes || "",
        risk: (d.risk as DeploymentRow["risk"]) || "medium",
      })) as DeploymentRow[];
    },
  });
}
