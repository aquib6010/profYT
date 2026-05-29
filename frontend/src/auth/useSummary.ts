// Dashboard summary, backed by GET /api/analytics/summary.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface CategoryRevenue {
  category: string;
  revenue_usd: number;
}

export interface AnalyticsSummary {
  channel: { display_name: string | null; channel_id: string | null };
  has_data: boolean;
  as_of: string | null;
  window_days: number;
  revenue_last_30d: number;
  revenue_prev_30d: number;
  revenue_change_pct: number | null;
  views_last_30d: number;
  videos_tracked: number;
  top_category: CategoryRevenue | null;
}

export function useSummary() {
  return useQuery<AnalyticsSummary>({
    queryKey: ["analytics", "summary"],
    queryFn: () => apiFetch<AnalyticsSummary>("/api/analytics/summary"),
    staleTime: 60_000,
  });
}
