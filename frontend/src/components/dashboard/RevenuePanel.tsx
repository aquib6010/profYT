import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";
import { ForecastChart } from "../charts/ForecastChart";
import type { ForecastPoint } from "../../lib/preview";
import { Skeleton, PanelMessage } from "./states";
import { useForecast } from "../../data/useForecast";
import { usd } from "../../lib/format";

const MODEL_LABEL: Record<string, string> = {
  ets: "Holt-Winters ETS",
  naive: "Naive baseline",
  seasonal_naive: "Seasonal naive",
  prophet: "Prophet",
  lightgbm: "LightGBM",
};

/**
 * Primary revenue chart. History + forecast + conformal band all come from the
 * real /api/forecast endpoint (model chosen by backtested MAE).
 */
export function RevenuePanel() {
  const { data: fc, isLoading, isError } = useForecast(14);

  // Adapt the API response to the chart's ForecastPoint shape.
  const series: ForecastPoint[] = [];
  if (fc?.has_forecast) {
    for (const h of fc.history) {
      series.push({ date: h.date, actual: round2(h.value), yhat: null, band: null });
    }
    const last = series[series.length - 1];
    if (last) {
      last.yhat = last.actual;
      last.band = [last.actual!, last.actual!];
    }
    for (const p of fc.forecast) {
      series.push({ date: p.date, actual: null, yhat: p.yhat, band: [p.lower, p.upper] });
    }
  }

  const bt = fc?.backtest;
  const modelName = fc?.model ? (MODEL_LABEL[fc.model] ?? fc.model) : null;
  const intervalPct = fc ? Math.round(fc.interval * 100) : 90;

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink">Revenue &amp; forecast</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Recent revenue with a 14-day projection and a {intervalPct}% prediction interval.
          </p>
        </div>
        {modelName && (
          <Badge tone="accent">
            {modelName} · {intervalPct}% conformal
          </Badge>
        )}
      </div>

      <div className="mt-5">
        {isLoading && <Skeleton className="h-[300px] w-full rounded-md" />}
        {isError && (
          <PanelMessage
            tone="error"
            title="Couldn't load the forecast"
            body="The forecast endpoint didn't respond."
          />
        )}
        {fc && !isError && !fc.has_forecast && (
          <div className="flex h-[300px] items-center justify-center text-center text-sm text-ink-muted">
            {fc.low_data
              ? "Not enough history to forecast yet — keep collecting data."
              : "No revenue data to forecast in this window."}
          </div>
        )}
        {fc?.has_forecast && series.length > 0 && <ForecastChart data={series} height={300} />}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-line pt-4 font-mono text-[11px] text-ink-subtle">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 bg-ink" /> Actual
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-accent" /> Forecast
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-4 rounded-sm bg-accent/20" /> {intervalPct}% interval
        </span>
        {bt && (
          <span className="ml-auto normal-case text-ink-muted">
            Backtest MAE <span className="text-ink tnum">{usd(bt.mae, { cents: true })}</span>
            {bt.beats_naive && <span className="text-pos"> · beats naive</span>}
            {bt.coverage !== null && (
              <span className="text-ink-subtle"> · {Math.round(bt.coverage * 100)}% coverage</span>
            )}
          </span>
        )}
      </div>
    </Card>
  );
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
