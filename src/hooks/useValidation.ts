import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ValidationSummary {
  fix_recommendation_id: string;
  before_ticket_count: number;
  before_customer_count: number;
  before_revenue_risk: number;
  after_ticket_count: number;
  after_customer_count: number;
  after_revenue_risk: number;
  deflection_pct: number;
  revenue_recovered_usd: number;
  status: string; // 'Success' | 'Partial Success' | 'Failed'
  loop_closed: boolean;
  measurement_count: number;
}

export function useValidation(recommendationId?: string) {
  const result = useQuery({
    queryKey: ["validation", "detail", recommendationId],
    queryFn: async () => {
      const { data } = await api.get<ValidationSummary>(`/ai/validate/${recommendationId}`);
      return data;
    },
    enabled: !!recommendationId,
    retry: false, // Don't retry if it returns 404 (no validation yet)
  });

  return result;
}

export function useRunValidationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      recommendationId,
      forceRevalidate = false,
    }: {
      recommendationId: string;
      forceRevalidate?: boolean;
    }) => {
      const { data } = await api.post<ValidationSummary>("/ai/validate", {
        fix_recommendation_id: recommendationId,
        force_revalidate: forceRevalidate,
      });
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["validation", "detail", variables.recommendationId],
      });
      queryClient.setQueryData(["validation", "detail", variables.recommendationId], data);
    },
  });
}
