import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import { useSupabaseSync } from "./useSupabaseSync";

export interface ClusterOut {
  id: string;
  title: string;
  summary?: string;
  severity: "critical" | "high" | "medium" | "low";
  status: "open" | "in_progress" | "resolved";
  ticket_count: number;
  affected_customers: number;
  monthly_cost_usd: number;
  confidence?: number;
  product_area?: string;
  related_deploy_id?: string;
  first_seen_at?: string;
  last_seen_at?: string;
  root_cause?: string;
  ticket_trend?: Array<{ date: string; count: number }>;
  example_titles?: string[];
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export function useClusters(page = 1, size = 20, severity?: string, status?: string) {
  // Sync automatically when ticket_clusters changes in Supabase
  useSupabaseSync("ticket_clusters", [queryKeys.clusters.all()]);

  const result = useQuery({
    queryKey: queryKeys.clusters.list({ page, size, severity, status }),
    queryFn: async () => {
      const { data } = await api.get<ClusterOut[]>("/ai/cluster", {
        params: { page, size, severity, status },
      });
      return data;
    },
  });

  return result;
}

export function useCluster(id: string) {
  useSupabaseSync("ticket_clusters", [queryKeys.clusters.detail(id)]);

  return useQuery({
    queryKey: queryKeys.clusters.detail(id),
    queryFn: async () => {
      const { data } = await api.get<ClusterOut>(`/ai/cluster/${id}`);
      return data;
    },
    enabled: !!id,
  });
}
