import { Card } from "../../ui/Card";
import { Skeleton } from "./states";
import { useAnomalies } from "../../data/useAnomalies";
import { shortDate } from "../../lib/format";
import { cn } from "../../lib/cn";

const sevTone: Record<string, string> = {
  high: "bg-neg-soft text-neg",
  medium: "bg-accent-soft text-accent-strong",
  low: "bg-pos-soft text-pos",
};

export function AnomalyFeed() {
  const { data, isLoading, isError } = useAnomalies();

  return (
    <Card className="flex h-full flex-col p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg font-semibold text-ink">Alerts</h2>
        <span className="font-mono text-xs text-ink-subtle">
          {data?.detectors.length ? "Isolation Forest · PELT · KL" : "anomaly detection"}
        </span>
      </div>

      {isLoading && (
        <div className="mt-4 space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <div className="mt-4 text-sm text-ink-muted">Couldn't load alerts.</div>
      )}

      {data && data.items.length === 0 && (
        <div className="mt-4 flex flex-1 items-center justify-center text-center text-sm text-ink-muted">
          No anomalies detected in the recent window.
        </div>
      )}

      {data && data.items.length > 0 && (
        <ul className="mt-4 space-y-3">
          {data.items.map((a) => (
            <li key={a.id} className="rounded-md border border-line p-3">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "rounded-sm px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide",
                    sevTone[a.severity] ?? sevTone.low,
                  )}
                >
                  {a.severity}
                </span>
                <span className="text-sm font-medium text-ink">{a.metric}</span>
                <span
                  className={cn(
                    "ml-auto font-mono text-sm font-semibold tnum",
                    a.delta < 0 ? "text-neg" : "text-pos",
                  )}
                >
                  {a.delta > 0 ? "+" : ""}
                  {a.delta}%
                </span>
              </div>
              <p className="mt-1.5 text-xs text-ink-muted">{a.cause}</p>
              <div className="mt-1 flex items-center gap-2 font-mono text-[11px] text-ink-subtle">
                <span>{shortDate(a.date)}</span>
                <span className="ml-auto truncate">{a.method}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
