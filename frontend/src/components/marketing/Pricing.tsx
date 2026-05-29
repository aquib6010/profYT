import { Section } from "../../ui/Section";
import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";
import { ButtonLink } from "../../ui/Button";
import { loginUrl } from "../../auth/useAuth";
import { cn } from "../../lib/cn";

// Placeholder pricing — not final.
const tiers = [
  {
    name: "Starter",
    price: "$0",
    cadence: "/mo",
    blurb: "For new creators connecting their first channel.",
    features: ["1 channel", "30-day revenue history", "Forecast + basic alerts", "Weekly refresh"],
    cta: "Connect free",
    featured: false,
  },
  {
    name: "Pro",
    price: "$19",
    cadence: "/mo",
    blurb: "For monetized creators running their channel like a business.",
    features: [
      "Unlimited history",
      "Anomaly alerts with causes",
      "Causal recommendations",
      "Per-video profitability",
      "Daily refresh",
    ],
    cta: "Start Pro",
    featured: true,
  },
  {
    name: "Studio",
    price: "$49",
    cadence: "/mo",
    blurb: "For multi-channel networks and teams.",
    features: ["Up to 10 channels", "Team seats", "Export & API access", "Priority support"],
    cta: "Talk to us",
    featured: false,
  },
];

export function Pricing() {
  return (
    <Section
      id="pricing"
      eyebrow="Pricing"
      title="Start free. Upgrade when it pays for itself."
      center
    >
      <div className="mt-14 grid items-start gap-5 lg:grid-cols-3">
        {tiers.map((t) => (
          <Card
            key={t.name}
            className={cn(
              "flex flex-col p-7",
              t.featured && "relative border-accent/40 shadow-md ring-1 ring-accent/20",
            )}
          >
            {t.featured && (
              <div className="absolute right-6 top-6">
                <Badge tone="accent">Most popular</Badge>
              </div>
            )}
            <div className="font-display text-lg font-semibold text-ink">{t.name}</div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="font-mono text-4xl font-semibold text-ink tnum">{t.price}</span>
              <span className="text-ink-subtle">{t.cadence}</span>
            </div>
            <p className="mt-2 text-sm text-ink-muted">{t.blurb}</p>
            <ul className="mt-6 space-y-3 text-sm">
              {t.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-ink">
                  <span className="mt-1 text-accent" aria-hidden>
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>
            <div className="mt-8">
              <ButtonLink
                href={loginUrl}
                variant={t.featured ? "primary" : "secondary"}
                className="w-full"
              >
                {t.cta}
              </ButtonLink>
            </div>
          </Card>
        ))}
      </div>
      <p className="mt-6 text-center font-mono text-xs text-ink-subtle">
        Placeholder pricing — for layout only.
      </p>
    </Section>
  );
}
