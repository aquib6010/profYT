import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastPoint } from "../../lib/preview";
import { shortDate, usd } from "../../lib/format";

/** Tooltip that shows the actual or forecast value + the interval, ignoring the raw band series. */
function ForecastTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const p: ForecastPoint = payload[0].payload;
  const value = p.actual ?? p.yhat;
  if (value == null) return null;
  return (
    <div className="rounded-md border border-line bg-surface px-3 py-2 text-xs shadow-md">
      <div className="font-mono text-ink-subtle">{shortDate(label as string)}</div>
      <div className="mt-1 font-medium text-ink tnum">
        {p.actual != null ? "Actual " : "Forecast "}
        {usd(value, { cents: true })}
      </div>
      {p.band && p.actual == null && (
        <div className="mt-0.5 font-mono text-[11px] text-ink-subtle tnum">
          {usd(p.band[0], { cents: true })} – {usd(p.band[1], { cents: true })}
        </div>
      )}
    </div>
  );
}

/**
 * Revenue history (solid ink line) + forecast (dashed amber line) with a
 * conformal confidence band (amber wash). `mini` strips axes/grid for use as a
 * hero/feature visual.
 */
export function ForecastChart({
  data,
  mini = false,
  height = 280,
}: {
  data: ForecastPoint[];
  mini?: boolean;
  height?: number;
}) {
  // The forecast starts at the first point that has a band but no actual.
  const splitIdx = data.findIndex((d) => d.actual === null);
  const splitDate = splitIdx > 0 ? data[splitIdx].date : undefined;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: mini ? 0 : 4 }}>
        {!mini && <CartesianGrid stroke="var(--line)" vertical={false} />}
        <defs>
          <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.18} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.04} />
          </linearGradient>
        </defs>

        <XAxis
          dataKey="date"
          hide={mini}
          tickFormatter={shortDate}
          tick={{ fontSize: 11, fill: "var(--ink-subtle)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--line)" }}
          minTickGap={28}
        />
        <YAxis
          hide={mini}
          width={44}
          tickFormatter={(v) => usd(v as number, { compact: true })}
          tick={{ fontSize: 11, fill: "var(--ink-subtle)" }}
          tickLine={false}
          axisLine={false}
        />

        {splitDate && !mini && (
          <ReferenceLine
            x={splitDate}
            stroke="var(--ink-subtle)"
            strokeDasharray="3 3"
            label={{ value: "forecast", position: "insideTopRight", fontSize: 10, fill: "var(--ink-subtle)" }}
          />
        )}

        <Area
          dataKey="band"
          stroke="none"
          fill="url(#bandFill)"
          isAnimationActive={!mini}
          connectNulls
        />
        <Line
          dataKey="actual"
          stroke="var(--ink)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={!mini}
          connectNulls={false}
        />
        <Line
          dataKey="yhat"
          stroke="var(--accent)"
          strokeWidth={2}
          strokeDasharray="5 4"
          dot={false}
          isAnimationActive={!mini}
          connectNulls={false}
        />

        {!mini && <Tooltip cursor={{ stroke: "var(--line)" }} content={<ForecastTooltip />} />}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
