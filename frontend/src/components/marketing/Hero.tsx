import { Link } from "react-router-dom";
import { Container } from "../../ui/Container";
import { ButtonLink, Button } from "../../ui/Button";
import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";
import { TrendBadge } from "../../ui/TrendBadge";
import { ForecastChart } from "../charts/ForecastChart";
import { useAuth, loginUrl } from "../../auth/useAuth";
import { revenueForecast } from "../../lib/preview";
import { usd } from "../../lib/format";

export function Hero() {
  const { isAuthenticated } = useAuth();
  const series = revenueForecast(11, 7.4, 30, 14);

  return (
    <section className="relative overflow-hidden bg-ledger">
      {/* warm wash behind the hero */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-gradient-to-b from-accent-soft/40 to-transparent"
      />
      <Container className="relative grid items-center gap-12 py-16 sm:py-24 lg:grid-cols-[1.05fr_1fr] lg:gap-10">
        <div className="animate-fade-up">
          <div className="inline-flex items-center gap-2 rounded-sm border border-line bg-surface/70 px-3 py-1 font-mono text-xs text-ink-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-pos" /> Revenue intelligence for creators
          </div>
          <h1 className="mt-5 text-display-lg font-bold text-ink sm:text-display-xl">
            Know which videos{" "}
            <span className="relative whitespace-nowrap text-accent">
              actually made
              <svg
                aria-hidden
                viewBox="0 0 300 12"
                className="absolute -bottom-1 left-0 w-full"
                preserveAspectRatio="none"
              >
                <path d="M2 9 C 80 2, 220 2, 298 8" stroke="var(--accent)" strokeWidth="2.5" fill="none" />
              </svg>
            </span>{" "}
            you money.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-muted">
            YouTube Studio shows you views. Profitly tells you profit — per-video revenue,
            calibrated earnings forecasts, and causal recommendations on what to make next.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button size="lg">Open your dashboard</Button>
              </Link>
            ) : (
              <ButtonLink href={loginUrl} size="lg">
                Connect your YouTube channel
              </ButtonLink>
            )}
            <a
              href="#how"
              className="inline-flex h-12 items-center px-2 text-sm font-medium text-ink-muted hover:text-ink"
            >
              See how it works →
            </a>
          </div>
          <p className="mt-4 font-mono text-xs text-ink-subtle">
            Read-only access · OAuth · tokens encrypted at rest
          </p>
        </div>

        {/* Product preview */}
        <div className="animate-fade-up [animation-delay:120ms]">
          <Card className="p-4 shadow-lg sm:p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-xs uppercase tracking-[0.12em] text-ink-subtle">
                  Revenue · 30-day forecast
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="font-mono text-2xl font-semibold text-ink tnum">
                    {usd(2480)}
                  </span>
                  <TrendBadge value={8.4} label="next 30d" />
                </div>
              </div>
              <Badge tone="preview">Preview</Badge>
            </div>
            <div className="mt-3">
              <ForecastChart data={series} height={240} />
            </div>
            <div className="mt-2 flex items-center gap-4 font-mono text-[11px] text-ink-subtle">
              <span className="flex items-center gap-1.5">
                <span className="h-0.5 w-4 bg-ink" /> Actual
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-0.5 w-4 border-t-2 border-dashed border-accent" /> Forecast
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-4 rounded-sm bg-accent/20" /> 90% interval
              </span>
            </div>
          </Card>
        </div>
      </Container>
    </section>
  );
}
