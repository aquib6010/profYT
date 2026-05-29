import { Section } from "../../ui/Section";
import { cn } from "../../lib/cn";

const steps = [
  {
    n: "1",
    title: "Connect your channel",
    body: "Sign in with Google and grant read-only access to your YouTube Analytics. Tokens are encrypted at rest — we never post or change anything.",
  },
  {
    n: "2",
    title: "Profitly analyzes the money",
    body: "We pull your per-video, per-day revenue and engagement, classify your content, and run the forecasting and causal models.",
  },
  {
    n: "3",
    title: "Get forecasts, alerts & actions",
    body: "Your dashboard fills in: next-30-day revenue with intervals, anomaly alerts with causes, and dollar-impact recommendations.",
  },
];

export function HowItWorks() {
  return (
    <Section
      id="how"
      eyebrow="How it works"
      title="Three steps to revenue clarity"
      center
      className="bg-surface-alt"
    >
      <ol className="mt-14 grid gap-6 md:grid-cols-3">
        {steps.map((s, i) => (
          <li key={s.n} className="relative">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-ink font-mono text-sm font-semibold text-paper">
                {s.n}
              </span>
              {i < steps.length - 1 && (
                <span aria-hidden className="hidden h-px flex-1 bg-line md:block" />
              )}
            </div>
            <h3 className={cn("mt-4 text-display-sm font-semibold text-ink")}>{s.title}</h3>
            <p className="mt-2 text-ink-muted leading-relaxed">{s.body}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
