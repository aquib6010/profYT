// Revenue forecast, backed by GET /api/forecast.

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

export interface FcHistoryPoint {
  date: string;
  value: number;
}
export interface FcPoint {
  date: string;
  yhat: number;
  lower: number;
  upper: number;
}
export interface BacktestInfo {
  mae: number;
  mape: number | null;
  naive_mae: number | null;
  beats_naive: boolean;
  coverage: number | null;
  n_origins: number;
  models_compared: string[];
}
export interface ForecastResponse {
  has_forecast: boolean;
  low_data: boolean;
  model: string | null;
  interval: number;
  as_of: string | null;
  history: FcHistoryPoint[];
  forecast: FcPoint[];
  backtest: BacktestInfo | null;
}

export function useForecast(horizon = 14) {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", horizon],
    queryFn: () => apiFetch<ForecastResponse>(`/api/forecast?horizon=${horizon}`),
    staleTime: 5 * 60_000,
  });
}
