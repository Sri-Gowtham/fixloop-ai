import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/queryKeys";

export interface DeploymentRow {
  id: string;
  version: string;
  title: string;
  date: string; // mapped from deployed_at
  notes?: string;
  risk: "critical" | "high" | "medium" | "low";
}

export function useDeployments(start?: string, end?: string) {
  return useQuery({
    queryKey: queryKeys.timeline.deployments({ start, end } as any),
    queryFn: async () => {
      let query = supabase
        .from("deployments")
        .select("*")
        .order("deployed_at", { ascending: false })
        .limit(20);

      if (start) {
        query = query.gte("deployed_at", start);
      }
      if (end) {
        query = query.lte("deployed_at", end);
      }

      const { data, error } = await query;
      
      if (error) {
        console.error("Failed to fetch deployments from Supabase", error);
        throw error;
      }

      return (data || []).map((d) => ({
        id: d.id,
        version: d.version || d.id,
        title: d.title,
        date: d.deployed_at ? new Date(d.deployed_at).toISOString().split('T')[0] : "",
        notes: d.notes,
        risk: d.risk || "medium",
      })) as DeploymentRow[];
    },
  });
}
