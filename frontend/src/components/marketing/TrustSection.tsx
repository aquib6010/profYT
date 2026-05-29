import { Section } from "../../ui/Section";
import { Card } from "../../ui/Card";

const pillars = [
  {
    title: "Calibrated uncertainty",
    body: "Forecasts ship with conformal prediction intervals. You see a range and its coverage — not a single number pretending to be certain.",
  },
  {
    title: "Benchmarked, not black-box",
    body: "Every model is scored against simple baselines with walk-forward validation. If a complex model doesn't beat the naive one, it doesn't ship.",
  },
  {
    title: "Causal, not just correlated",
    body: "Recommendations use doubly-robust uplift estimation with sensitivity analysis — built to survive the question 'but did that actually cause it?'",
  },
  {
    title: "Your data, locked down",
    body: "Read-only OAuth scopes, tokens encrypted at rest, and no third-party resale. We touch revenue data the way a bank touches money.",
  },
];

export function TrustSection() {
  return (
    <Section
      eyebrow="Built right"
      title="Numbers you can take to the bank"
      intro="This is a product about money, so the modelling is held to a money standard."
    >
      <div className="mt-12 grid gap-5 sm:grid-cols-2">
        {pillars.map((p) => (
          <Card key={p.title} className="p-6">
            <h3 className="font-display text-lg font-semibold text-ink">{p.title}</h3>
            <p className="mt-2 text-ink-muted leading-relaxed">{p.body}</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
