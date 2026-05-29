import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { cn } from "../lib/cn";

/** Tiny trend line for stat cards. Tone drives the stroke colour. */
export function Sparkline({
  data,
  tone = "accent",
  className,
}: {
  data: number[];
  tone?: "accent" | "pos" | "neg";
  className?: string;
}) {
  const color =
    tone === "pos" ? "var(--pos)" : tone === "neg" ? "var(--neg)" : "var(--accent)";
  const rows = data.map((value, i) => ({ i, value }));
  const id = `spark-${tone}`;
  return (
    <div className={cn("h-10 w-full", className)} aria-hidden>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.22} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.75}
            fill={`url(#${id})`}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
