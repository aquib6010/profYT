import { Card } from "../../ui/Card";
import { Skeleton } from "./states";
import { useRecommendations } from "../../data/useRecommendations";
import { usd } from "../../lib/format";

export function RecommendationsPanel() {
  const { data, isLoading, isError } = useRecommendations();

  return (
    <Card className="flex h-full flex-col p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg font-semibold text-ink">Recommendations</h2>
        <span className="font-mono text-xs text-ink-subtle">
          {data?.method ? "Causal uplift" : "recommendations"}
        </span>
      </div>

      {isLoading && (
        <div className="mt-4 space-y-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      )}

      {isError && <div className="mt-4 text-sm text-ink-muted">Couldn't load recommendations.</div>}

      {data && data.items.length === 0 && (
        <div className="mt-4 flex flex-1 items-center justify-center text-center text-sm text-ink-muted">
          Not enough video history yet to estimate content-mix uplift.
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <ul className="mt-4 space-y-3">
            {data.items.map((r) => (
              <li key={r.id} className="rounded-md border border-line p-3">
                <div className="flex items-start justify-between gap-3">
                  <span className="text-sm font-medium text-ink">{r.action}</span>
                  <span className="shrink-0 font-mono text-sm font-semibold text-pos tnum">
                    +{usd(r.impact_usd)}/mo
                  </span>
                </div>
                <p className="mt-1.5 text-xs text-ink-muted">{r.detail}</p>
                <div className="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-ink-subtle tnum">
                  <span>
                    90% CI {usd(r.ci_low)}–{usd(r.ci_high)}
                  </span>
                  <span className="ml-auto uppercase tracking-wide">{r.confidence} confidence</span>
                </div>
              </li>
            ))}
          </ul>
          {data.method && (
            <p className="mt-3 font-mono text-[11px] text-ink-subtle">{data.method}</p>
          )}
        </>
      )}
    </Card>
  );
}
