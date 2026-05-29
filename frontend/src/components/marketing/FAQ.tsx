import { Section } from "../../ui/Section";
import { Accordion, type QA } from "../../ui/Accordion";

const faqs: QA[] = [
  {
    q: "Is my YouTube data safe?",
    a: "Profitly requests read-only access through Google OAuth. We never post, edit, or delete anything on your channel, and your access tokens are encrypted at rest. You can revoke access from your Google account at any time.",
  },
  {
    q: "Which accounts are supported?",
    a: "Any Google account that owns a YouTube channel with monetization data. Revenue figures require the YouTube Analytics monetary scope, which you grant during sign-in.",
  },
  {
    q: "How accurate are the forecasts?",
    a: "Forecasts come from an ensemble validated with walk-forward backtesting against simple baselines, and every prediction includes a calibrated confidence interval so you can see the uncertainty, not just a point estimate.",
  },
  {
    q: "Do I need a big channel for this to work?",
    a: "No. Smaller channels get the most value from spotting which content actually pays. Forecast intervals simply widen when there's less history — they stay honest about what the data can support.",
  },
  {
    q: "How is this different from YouTube Studio?",
    a: "Studio reports what happened — views, watch time, a single revenue total. Profitly attributes revenue to individual videos and content types, forecasts where you're headed, and recommends what to make next with a dollar estimate.",
  },
  {
    q: "How often does data refresh?",
    a: "Daily on paid plans and weekly on the free tier. Ingestion runs on a schedule and backfills history when you first connect.",
  },
];

export function FAQ() {
  return (
    <Section id="faq" eyebrow="FAQ" title="Questions, answered" className="bg-surface-alt">
      <div className="mt-10 max-w-3xl">
        <Accordion items={faqs} />
      </div>
    </Section>
  );
}
