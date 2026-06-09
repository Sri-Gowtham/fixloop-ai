/**
 * Strongly-typed Query Key Factory for React Query.
 * Centralises cache keys for easy invalidation.
 */

export const queryKeys = {
  dashboard: {
    all: () => ["dashboard"] as const,
    kpis: () => ["dashboard", "kpis"] as const,
  },
  clusters: {
    all: () => ["clusters"] as const,
    list: (filters?: any) => ["clusters", "list", { filters }] as const,
    detail: (id: string) => ["clusters", "detail", id] as const,
  },
  timeline: {
    all: () => ["timeline"] as const,
    deployments: (dateRange?: { start: string; end: string }) => 
      ["timeline", "deployments", { dateRange }] as const,
  },
  investigations: {
    all: () => ["investigations"] as const,
    byCluster: (clusterId: string) => ["investigations", "byCluster", clusterId] as const,
    detail: (id: string) => ["investigations", "detail", id] as const,
  },
  recommendations: {
    all: () => ["recommendations"] as const,
    byInvestigation: (investigationId: string) => ["recommendations", "byInvestigation", investigationId] as const,
    detail: (id: string) => ["recommendations", "detail", id] as const,
  },
  validation: {
    all: () => ["validation"] as const,
    detail: (recommendationId: string) => ["validation", "detail", recommendationId] as const,
  },
};
