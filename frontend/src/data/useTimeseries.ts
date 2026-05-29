// Daily revenue/views/cpm series, backed by GET /api/analytics/timeseries.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface TimeseriesPoint {
  date: string;
  revenue: number;
  views: number;
  cpm: number | null;
}

export interface Timeseries {
  as_of: string | null;
  points: TimeseriesPoint[];
}

export function useTimeseries(days = 45) {
  return useQuery<Timeseries>({
    queryKey: ["analytics", "timeseries", days],
    queryFn: () => apiFetch<Timeseries>(`/api/analytics/timeseries?days=${days}`),
    staleTime: 60_000,
  });
}
