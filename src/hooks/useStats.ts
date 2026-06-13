import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface StatsOut {
  total_tickets: number;
  active_clusters: number;
  revenue_risk_usd: number;
  recommendations_generated: number;
  fix_success_rate_pct: number;
  deployments_tracked: number;
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: async () => {
      const response = await api.get("/ai/stats");
      return response.data as StatsOut;
    },
  });
}
