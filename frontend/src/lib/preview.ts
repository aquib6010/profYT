// Synthetic, deterministic preview data for product surfaces whose real
// endpoints don't exist yet (forecast, anomalies, recommendations, per-video
// table, sparklines). Everything here is clearly labelled "Preview" in the UI.
//
// Seeded RNG so the visuals are stable across reloads. When the backend ships
// the corresponding endpoints, swap these generators for real fetches — the
// component prop shapes are designed to match the planned API.

function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function isoDaysAgo(anchor: Date, back: number): string {
  const d = new Date(anchor);
  d.setDate(d.getDate() - back);
  return d.toISOString().slice(0, 10);
}

export interface ForecastPoint {
  date: string;
  actual: number | null;
  yhat: number | null;
  band: [number, number] | null; // conformal interval [lower, upper]
}

/**
 * History (actual) + forward forecast with a widening confidence band.
 * `dailyBase` lets the dashboard seed plausible magnitudes from real revenue.
 */
export function revenueForecast(
  seed = 7,
  dailyBase = 6,
  histDays = 30,
  fcDays = 14,
  anchor: Date = new Date(),
): ForecastPoint[] {
  const rnd = mulberry32(seed);
  const out: ForecastPoint[] = [];
  let level = dailyBase;

  // History
  const hist: number[] = [];
  for (let i = histDays - 1; i >= 0; i--) {
    const dow = (anchor.getDay() - i) % 7;
    const weekly = 1 + 0.18 * Math.cos((dow / 7) * 2 * Math.PI); // weekday lift
    const noise = 0.85 + rnd() * 0.3;
    const v = Math.max(0.5, level * weekly * noise);
    hist.push(v);
    out.push({ date: isoDaysAgo(anchor, i), actual: round2(v), yhat: null, band: null });
    level += (rnd() - 0.45) * 0.25; // gentle drift
  }

  // Junction: forecast starts where actual ends
  const last = out[out.length - 1];
  last.yhat = last.actual;
  last.band = [last.actual!, last.actual!];

  // Forecast — trend continues, band widens with horizon
  let yhat = hist[hist.length - 1];
  const trend = (hist[hist.length - 1] - hist[0]) / histDays;
  for (let i = 1; i <= fcDays; i++) {
    yhat = Math.max(0.5, yhat + trend * 0.6 + (rnd() - 0.5) * 0.2);
    const spread = yhat * (0.06 + i * 0.018);
    out.push({
      date: isoDaysAgo(anchor, -i),
      actual: null,
      yhat: round2(yhat),
      band: [round2(yhat - spread), round2(yhat + spread)],
    });
  }
  return out;
}

/**
 * Build a forecast chart series from REAL history points. The history (actual)
 * is real; the forward projection + widening band is a preview placeholder
 * until the forecast endpoint ships. Trend is a simple slope over the tail.
 */
export function forecastFromHistory(
  history: { date: string; value: number }[],
  fcDays = 14,
): ForecastPoint[] {
  if (history.length === 0) return [];

  const out: ForecastPoint[] = history.map((h) => ({
    date: h.date,
    actual: round2(h.value),
    yhat: null,
    band: null,
  }));

  // Junction: forecast departs from the last actual point.
  const last = out[out.length - 1];
  last.yhat = last.actual;
  last.band = [last.actual!, last.actual!];

  // Slope over the trailing window (up to 14 points).
  const tail = history.slice(-14);
  const slope = tail.length > 1 ? (tail[tail.length - 1].value - tail[0].value) / tail.length : 0;

  const anchorIso = history[history.length - 1].date;
  const [y, m, d] = anchorIso.split("-").map(Number);
  const anchor = new Date(y, m - 1, d);

  let yhat = history[history.length - 1].value;
  for (let i = 1; i <= fcDays; i++) {
    yhat = Math.max(0.5, yhat + slope * 0.6);
    const spread = Math.max(0.4, yhat * (0.06 + i * 0.018));
    const fd = new Date(anchor);
    fd.setDate(fd.getDate() + i);
    out.push({
      date: fd.toISOString().slice(0, 10),
      actual: null,
      yhat: round2(yhat),
      band: [round2(yhat - spread), round2(yhat + spread)],
    });
  }
  return out;
}

/** Small sparkline series for stat cards. */
export function sparkline(seed: number, points = 24, base = 10): number[] {
  const rnd = mulberry32(seed);
  let v = base;
  return Array.from({ length: points }, () => {
    v = Math.max(1, v + (rnd() - 0.45) * base * 0.25);
    return round2(v);
  });
}

export interface AnomalyItem {
  id: string;
  date: string;
  severity: "high" | "medium" | "low";
  metric: string;
  delta: number; // negative = drop
  cause: string;
}

export function anomalies(anchor: Date = new Date()): AnomalyItem[] {
  return [
    {
      id: "a1",
      date: isoDaysAgo(anchor, 3),
      severity: "high",
      metric: "Effective CPM",
      delta: -34,
      cause: "Audience mix shifted US → India; lower-CPM geography now dominant.",
    },
    {
      id: "a2",
      date: isoDaysAgo(anchor, 9),
      severity: "medium",
      metric: "Revenue / video",
      delta: -18,
      cause: "Three vlogs published in a row — vlogs monetize ~2.7× below tutorials.",
    },
    {
      id: "a3",
      date: isoDaysAgo(anchor, 16),
      severity: "low",
      metric: "Watch time",
      delta: +12,
      cause: "Tutorial back-catalog resurfaced in search; positive outlier.",
    },
  ];
}

export interface Recommendation {
  id: string;
  action: string;
  impact: number; // monthly $ delta
  ciLow: number;
  ciHigh: number;
  confidence: "high" | "medium";
}

export function recommendations(): Recommendation[] {
  return [
    {
      id: "r1",
      action: "Shift content mix toward 70% tutorials",
      impact: 612,
      ciLow: 410,
      ciHigh: 820,
      confidence: "high",
    },
    {
      id: "r2",
      action: "Publish on Tue/Wed to ride weekday CPM",
      impact: 145,
      ciLow: 60,
      ciHigh: 240,
      confidence: "medium",
    },
    {
      id: "r3",
      action: "Re-target US/UK audience in 2 upcoming reviews",
      impact: absToMonthly(98),
      ciLow: 30,
      ciHigh: 170,
      confidence: "medium",
    },
  ];
}

export interface VideoRow {
  id: string;
  title: string;
  category: string;
  views: number;
  revenue: number;
  rpm: number;
}

export function videos(seed = 21): VideoRow[] {
  const rnd = mulberry32(seed);
  const rows: Array<[string, string, number]> = [
    ["Master FastAPI in 10 minutes", "tutorial", 4.2],
    ["Complete Docker crash course", "tutorial", 4.0],
    ["System design explained step by step", "tutorial", 3.8],
    ["PyTorch honest review", "review", 3.1],
    ["My day vlog #14", "vlog", 1.0],
    ["Behind the scenes #7", "vlog", 0.9],
    ["SQL in 30 seconds #shorts", "shorts", 0.3],
    ["Channel update #3", "other", 1.4],
  ];
  return rows.map(([title, category, rpm], i) => {
    const views = Math.round((1500 + rnd() * 7000) * (category === "shorts" ? 3 : 1));
    return {
      id: `v${i}`,
      title,
      category,
      views,
      revenue: round2((views / 1000) * rpm),
      rpm,
    };
  });
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
function absToMonthly(n: number): number {
  return n;
}
