import type { ReactNode } from "react";
import { cn } from "../lib/cn";

type Tone = "neutral" | "accent" | "pos" | "neg" | "preview";

const tones: Record<Tone, string> = {
  neutral: "bg-ink/[0.06] text-ink-muted",
  accent: "bg-accent-soft text-accent-strong",
  pos: "bg-pos-soft text-pos",
  neg: "bg-neg-soft text-neg",
  preview: "border border-dashed border-line text-ink-subtle",
};

/** Small pill. The `preview` tone flags not-yet-wired, synthetic-data surfaces. */
export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm px-2 py-0.5 font-mono text-[11px] uppercase tracking-[0.1em]",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
