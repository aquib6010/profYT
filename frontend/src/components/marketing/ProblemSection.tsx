import { Section } from "../../ui/Section";
import { Card } from "../../ui/Card";
import { cn } from "../../lib/cn";

const studio = [
  "Views, watch time, impressions",
  "One lump revenue number",
  "Per-video stats in isolation",
  "What happened, after the fact",
];
const profitly = [
  "Revenue attributed to each video",
  "Which content types actually pay",
  "A forecast of next month's earnings",
  "What to make next — with a $ estimate",
];

export function ProblemSection() {
  return (
    <Section
      id="problem"
      eyebrow="The gap"
      title={
        <>
          Studio shows you <span className="text-ink-subtle">what</span> happened.
          <br />
          Profitly tells you <span className="text-accent">why</span> — and what to do.
        </>
      }
      intro="Creators make six-figure decisions on a dashboard built for watch time, not for money."
    >
      <div className="mt-12 grid gap-5 md:grid-cols-2">
        <Compare title="YouTube Studio" tone="muted" items={studio} />
        <Compare title="Profitly" tone="accent" items={profitly} />
      </div>
    </Section>
  );
}

function Compare({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "muted" | "accent";
}) {
  const accent = tone === "accent";
  return (
    <Card className={cn("p-7", accent && "border-accent/30 bg-surface-alt")}>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "font-display text-lg font-semibold",
            accent ? "text-accent" : "text-ink-muted",
          )}
        >
          {title}
        </span>
      </div>
      <ul className="mt-5 space-y-3">
        {items.map((it) => (
          <li key={it} className="flex items-start gap-3 text-ink">
            <span
              aria-hidden
              className={cn(
                "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm font-mono text-xs",
                accent ? "bg-pos-soft text-pos" : "bg-ink/[0.06] text-ink-subtle",
              )}
            >
              {accent ? "✓" : "•"}
            </span>
            <span className={cn(!accent && "text-ink-muted")}>{it}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
