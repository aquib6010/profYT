// Per-video profitability rows, backed by GET /api/videos.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface VideoRow {
  id: number;
  title: string;
  category: string;
  views: number;
  revenue_usd: number;
  rpm_usd: number;
}

export function useVideos() {
  return useQuery<VideoRow[]>({
    queryKey: ["videos"],
    queryFn: () => apiFetch<VideoRow[]>("/api/videos"),
    staleTime: 60_000,
  });
}
