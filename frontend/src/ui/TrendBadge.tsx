import { cn } from "../lib/cn";

/**
 * Trend indicator for a percentage delta. Green = up, red = down — used as a
 * data signal, never decoration. `invert` flags cases where down is good.
 */
export function TrendBadge({
  value,
  label,
  invert = false,
  className,
}: {
  value: number | null;
  label?: string;
  invert?: boolean;
  className?: string;
}) {
  if (value === null) return null;
  const good = invert ? value < 0 : value >= 0;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 font-mono text-xs font-medium tnum",
        good ? "bg-pos-soft text-pos" : "bg-neg-soft text-neg",
        className,
      )}
    >
      <span aria-hidden>{value >= 0 ? "▲" : "▼"}</span>
      {Math.abs(value).toFixed(1)}%
      {label && <span className="text-ink-subtle font-sans font-normal">{label}</span>}
    </span>
  );
}
