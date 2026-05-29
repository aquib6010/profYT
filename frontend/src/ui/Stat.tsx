import type { ReactNode } from "react";
import { Card } from "./Card";
import { Sparkline } from "./Sparkline";
import { cn } from "../lib/cn";

/**
 * Headline metric: small label, big mono number, optional trend + sparkline.
 * The big figure uses tabular mono so columns of stats align.
 */
export function Stat({
  label,
  value,
  trend,
  footnote,
  spark,
  sparkTone = "accent",
  className,
}: {
  label: string;
  value: ReactNode;
  trend?: ReactNode;
  footnote?: ReactNode;
  spark?: number[];
  sparkTone?: "accent" | "pos" | "neg";
  className?: string;
}) {
  return (
    <Card className={cn("flex flex-col p-5", className)}>
      <div className="flex items-start justify-between gap-3">
        <span className="font-mono text-xs uppercase tracking-[0.12em] text-ink-subtle">
          {label}
        </span>
        {trend}
      </div>
      <div className="mt-3 font-mono text-3xl font-semibold tracking-tight text-ink tnum">
        {value}
      </div>
      {spark && <Sparkline data={spark} tone={sparkTone} className="mt-3" />}
      {footnote && <div className="mt-2 text-xs text-ink-muted">{footnote}</div>}
    </Card>
  );
}
