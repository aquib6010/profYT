import type { ReactNode } from "react";
import { Section } from "../../ui/Section";
import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";
import { ForecastChart } from "../charts/ForecastChart";
import { revenueForecast } from "../../lib/preview";
import { cn } from "../../lib/cn";
import { usd } from "../../lib/format";

export function Features() {
  return (
    <Section
      id="features"
      eyebrow="What you get"
      title="Five answers Studio can't give you"
      intro="Each one leads with the question it answers in plain language. The ML is the footnote; the decision is the headline."
    >
      <div className="mt-14 space-y-6">
        <FeatureRow
          n="01"
          question="Will I hit my number next month?"
          name="Revenue forecast"
          body="An ensemble (Prophet, LightGBM, gradient baselines) projects your next 30 days with a calibrated confidence interval — not a single optimistic line."
          visual={<ForecastChart data={revenueForecast(3, 6.6, 24, 12)} mini height={180} />}
        />
        <FeatureRow
          n="02"
          question="What just broke, and why?"
          name="Anomaly detection"
          reverse
          body="Profitly flags revenue and CPM shocks the moment they happen and attributes the cause — so a drop reads 'audience shifted to lower-CPM geos,' not just a red number."
          visual={<AnomalyVisual />}
        />
        <FeatureRow
          n="03"
          question="What kind of videos are these, really?"
          name="Content categorization"
          body="Every upload is auto-classified — tutorial, vlog, review, shorts — using semantic embeddings, so revenue can be grouped by what you actually make."
          visual={<CategoryVisual />}
        />
        <FeatureRow
          n="04"
          question="What should I make more of?"
          name="Uplift recommendations"
          reverse
          body="Causal uplift estimation turns correlation into a recommendation with a dollar figure and a confidence range — backed by sensitivity analysis, not vibes."
          visual={<UpliftVisual />}
        />
        <FeatureRow
          n="05"
          question="Is my audience quietly changing?"
          name="Audience drift"
          body="Rolling divergence on your geography and viewer mix surfaces slow shifts before they show up in your paycheck."
          visual={<DriftVisual />}
        />
      </div>
    </Section>
  );
}

function FeatureRow({
  n,
  question,
  name,
  body,
  visual,
  reverse = false,
}: {
  n: string;
  question: string;
  name: string;
  body: string;
  visual: ReactNode;
  reverse?: boolean;
}) {
  return (
    <Card interactive className="grid gap-6 p-6 md:grid-cols-2 md:gap-10 md:p-8">
      <div className={cn("flex flex-col justify-center", reverse && "md:order-2")}>
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm text-accent">{n}</span>
          <Badge tone="neutral">{name}</Badge>
        </div>
        <h3 className="mt-3 text-display-sm font-semibold text-ink">{question}</h3>
        <p className="mt-3 text-ink-muted leading-relaxed">{body}</p>
      </div>
      <div className={cn("flex items-center", reverse && "md:order-1")}>
        <div className="w-full rounded-md border border-line bg-surface-alt p-4">{visual}</div>
      </div>
    </Card>
  );
}

function AnomalyVisual() {
  return (
    <div className="space-y-2.5">
      {[
        { sev: "High", m: "Effective CPM −34%", c: "US → India audience shift", tone: "neg" as const },
        { sev: "Med", m: "Revenue / video −18%", c: "vlog streak vs. tutorials", tone: "neg" as const },
        { sev: "Low", m: "Watch time +12%", c: "search resurfacing", tone: "pos" as const },
      ].map((a) => (
        <div key={a.m} className="flex items-center gap-3 rounded-sm bg-surface px-3 py-2">
          <span
            className={cn(
              "font-mono text-[10px] uppercase",
              a.tone === "neg" ? "text-neg" : "text-pos",
            )}
          >
            {a.sev}
          </span>
          <span className="text-sm font-medium text-ink tnum">{a.m}</span>
          <span className="ml-auto truncate text-xs text-ink-subtle">{a.c}</span>
        </div>
      ))}
    </div>
  );
}

function CategoryVisual() {
  const cats = [
    { name: "Tutorial", pct: 100, rpm: "$4.0" },
    { name: "Review", pct: 76, rpm: "$3.0" },
    { name: "Vlog", pct: 25, rpm: "$1.0" },
    { name: "Shorts", pct: 8, rpm: "$0.3" },
  ];
  return (
    <div className="space-y-3">
      {cats.map((c) => (
        <div key={c.name}>
          <div className="flex justify-between text-xs">
            <span className="text-ink">{c.name}</span>
            <span className="font-mono text-ink-subtle tnum">{c.rpm} RPM</span>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-ink/[0.06]">
            <div className="h-full rounded-full bg-accent" style={{ width: `${c.pct}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function UpliftVisual() {
  return (
    <div className="text-center">
      <div className="text-sm text-ink-muted">Shift to 70% tutorials</div>
      <div className="mt-1 font-mono text-3xl font-semibold text-pos tnum">+{usd(612)}/mo</div>
      <div className="mt-4">
        <div className="relative mx-auto h-2 w-3/4 rounded-full bg-pos-soft">
          <div className="absolute inset-y-0 left-[28%] right-[18%] rounded-full bg-pos/40" />
          <div className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-pos" />
        </div>
        <div className="mt-1.5 flex justify-between font-mono text-[11px] text-ink-subtle tnum">
          <span>{usd(410)}</span>
          <span>90% CI</span>
          <span>{usd(820)}</span>
        </div>
      </div>
    </div>
  );
}

function DriftVisual() {
  const before = [["US", 50], ["IN", 20], ["BR", 10], ["GB", 10], ["DE", 10]] as const;
  const after = [["IN", 50], ["US", 25], ["BR", 10], ["DE", 10], ["GB", 5]] as const;
  const palette = ["bg-accent", "bg-ink", "bg-ink-subtle", "bg-pos", "bg-neg"];
  const Bar = ({ rows, label }: { rows: readonly (readonly [string, number])[]; label: string }) => (
    <div>
      <div className="mb-1 font-mono text-[11px] text-ink-subtle">{label}</div>
      <div className="flex h-3 overflow-hidden rounded-full">
        {rows.map(([c, v], i) => (
          <div key={c} className={palette[i]} style={{ width: `${v}%` }} title={`${c} ${v}%`} />
        ))}
      </div>
    </div>
  );
  return (
    <div className="space-y-3">
      <Bar rows={before} label="Audience · 60 days ago" />
      <Bar rows={after} label="Audience · today" />
      <div className="text-xs text-neg">↳ US share −25pts → weighted CPM falling</div>
    </div>
  );
}
