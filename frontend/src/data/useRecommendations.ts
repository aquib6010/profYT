// Uplift recommendations, backed by GET /api/recommendations.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface Recommendation {
  id: string;
  action: string;
  impact_usd: number;
  ci_low: number;
  ci_high: number;
  confidence: "high" | "medium";
  detail: string;
}

export interface RecommendationsResponse {
  has_data: boolean;
  items: Recommendation[];
  method: string;
}

export function useRecommendations() {
  return useQuery<RecommendationsResponse>({
    queryKey: ["recommendations"],
    queryFn: () => apiFetch<RecommendationsResponse>("/api/recommendations"),
    staleTime: 5 * 60_000,
  });
}
