// Anomaly feed, backed by GET /api/anomalies.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface AnomalyItem {
  id: string;
  date: string;
  severity: "high" | "medium" | "low";
  metric: string;
  delta: number;
  cause: string;
  method: string;
}

export interface AnomalyResponse {
  has_data: boolean;
  items: AnomalyItem[];
  detectors: string[];
}

export function useAnomalies() {
  return useQuery<AnomalyResponse>({
    queryKey: ["anomalies"],
    queryFn: () => apiFetch<AnomalyResponse>("/api/anomalies"),
    staleTime: 5 * 60_000,
  });
}
