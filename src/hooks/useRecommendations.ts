import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface RecommendationOut {
  id: string;
  cluster_id: string;
  investigation_id?: string;
  title: string;
  description: string;
  priority?: string;
  engineering_effort?: string;
  confidence_score?: number;
  expected_reduction_pct?: number;
  expected_recovery_usd?: number;
  actual_reduction_pct?: number;
  actual_recovery_usd?: number;
  before_ticket_count?: number;
  after_ticket_count?: number;
  estimated_eta?: string;
  jira_title?: string;
  jira_description?: string;
  jira_acceptance_criteria?: string[];
  jira_severity?: string;
  status: string;
}

export function useRecommendations(investigationId?: string) {
  return useQuery({
    queryKey: ["recommendations", "byInvestigation", investigationId],
    queryFn: async () => {
      const { data } = await api.get<RecommendationOut[]>(
        `/ai/recommend/investigation/${investigationId}`,
      );
      return data[0] || null;
    },
    enabled: !!investigationId,
  });
}

export function useAllRecommendations() {
  return useQuery({
    queryKey: ["recommendations", "all"],
    queryFn: async () => {
      const { data } = await api.get<RecommendationOut[]>("/ai/recommend");
      return data;
    },
  });
}

export function useGenerateRecommendationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      investigationId,
      clusterId,
    }: {
      investigationId: string;
      clusterId: string;
    }) => {
      const { data } = await api.post<RecommendationOut>("/ai/recommend", {
        investigation_id: investigationId,
        cluster_id: clusterId,
        force_refresh: true,
      });
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["recommendations", "byInvestigation", variables.investigationId],
      });
      queryClient.invalidateQueries({ queryKey: ["recommendations", "all"] });
    },
  });
}
