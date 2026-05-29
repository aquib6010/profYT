import { Stat } from "../../ui/Stat";
import { TrendBadge } from "../../ui/TrendBadge";
import type { AnalyticsSummary } from "../../auth/useSummary";
import { useTimeseries } from "../../data/useTimeseries";
import { usd, compact, titleCase } from "../../lib/format";

/**
 * Real metrics from /api/analytics/summary, with sparklines drawn from the real
 * daily timeseries (same query the revenue chart uses — React Query dedupes it).
 */
export function StatCards({ data }: { data: AnalyticsSummary }) {
  const { data: ts } = useTimeseries(45);
  const points = ts?.points ?? [];
  const revSpark = points.slice(-24).map((p) => p.revenue);
  const viewSpark = points.slice(-24).map((p) => p.views);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Stat
        label="Revenue · 30d"
        value={usd(data.revenue_last_30d)}
        trend={<TrendBadge value={data.revenue_change_pct} />}
        spark={revSpark.length ? revSpark : undefined}
        sparkTone={data.revenue_change_pct !== null && data.revenue_change_pct < 0 ? "neg" : "pos"}
        footnote={`vs ${usd(data.revenue_prev_30d)} prior 30d`}
      />
      <Stat
        label="Views · 30d"
        value={compact(data.views_last_30d)}
        spark={viewSpark.length ? viewSpark : undefined}
        sparkTone="accent"
        footnote={`${data.videos_tracked} videos tracked`}
      />
      <Stat
        label="Videos tracked"
        value={data.videos_tracked.toLocaleString()}
        footnote={data.as_of ? `as of ${data.as_of}` : undefined}
      />
      <Stat
        label="Top category"
        value={data.top_category ? titleCase(data.top_category.category) : "—"}
        footnote={
          data.top_category ? `${usd(data.top_category.revenue_usd)} in window` : "no data yet"
        }
      />
    </div>
  );
}
