import { cn } from "../lib/cn";

/** Profitly wordmark: a small ledger-bar mark + display-face name. */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span aria-hidden className="flex h-7 w-7 items-end justify-center gap-[2px] rounded-md bg-ink px-1.5 pb-1.5">
        <i className="block w-[3px] rounded-sm bg-accent" style={{ height: "40%" }} />
        <i className="block w-[3px] rounded-sm bg-paper" style={{ height: "65%" }} />
        <i className="block w-[3px] rounded-sm bg-accent" style={{ height: "90%" }} />
      </span>
      <span className="font-display text-lg font-bold tracking-tight text-ink">Profitly</span>
    </span>
  );
}
