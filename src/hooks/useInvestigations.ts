import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export interface DeployCorrelation {
  deploy_id: string;
  version: string;
  deployed_at: string;
  title: string;
  correlation: number;
}

export interface SimulationResult {
  before_ticket_count: number;
  after_ticket_count: number;
  deflection_pct: number;
  recovered_usd: number;
}

export interface EvidenceOut {
  id: string;
  evidence_type: string;
  title: string;
  detail?: string;
  weight: number;
  sort_order: number;
}

export interface InvestigationOut {
  id: string;
  cluster_id: string;
  root_cause: string;
  confidence: number;
  impact_level: string;
  affected_customers: number;
  revenue_impact_usd: number;
  deploy_correlation?: DeployCorrelation;
  reasoning_steps: string[];
  evidence: EvidenceOut[];
  simulation?: SimulationResult;
  created_at: string;
}

export function useInvestigation(id: string) {
  return useQuery({
    queryKey: queryKeys.investigations.detail(id),
    queryFn: async () => {
      const { data } = await api.get<InvestigationOut>(`/ai/investigate/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useInvestigationByCluster(clusterId: string) {
  return useQuery({
    queryKey: queryKeys.investigations.byCluster(clusterId),
    queryFn: async () => {
      const { data } = await api.get<InvestigationOut[]>(`/ai/investigate/cluster/${clusterId}`);
      // The API returns a list (newest first). We can just return the first one as the active investigation.
      return data[0] || null;
    },
    enabled: !!clusterId,
  });
}

export function useRunInvestigationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      clusterId,
      forceRefresh = false,
    }: {
      clusterId: string;
      forceRefresh?: boolean;
    }) => {
      const { data } = await api.post<InvestigationOut>("/ai/investigate", {
        cluster_id: clusterId,
        force_refresh: forceRefresh,
        confidence_threshold: 0.7,
        deploy_correlation_days: 7,
      });
      return data;
    },
    onSuccess: (data, variables) => {
      // Invalidate cluster-specific and general investigation queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.investigations.byCluster(variables.clusterId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.investigations.all() });
      if (data?.id) {
        queryClient.setQueryData(queryKeys.investigations.detail(data.id), data);
      }
    },
  });
}
