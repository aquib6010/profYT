import type { ReactNode } from "react";
import { Card } from "../../ui/Card";
import { cn } from "../../lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md bg-ink/[0.06]",
        "after:absolute after:inset-0 after:-translate-x-full after:animate-[shimmer_1.4s_infinite]",
        "after:bg-gradient-to-r after:from-transparent after:via-surface/60 after:to-transparent",
        className,
      )}
    />
  );
}

export function StatCardsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="p-5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="mt-4 h-8 w-32" />
          <Skeleton className="mt-4 h-10 w-full" />
        </Card>
      ))}
    </div>
  );
}

export function PanelMessage({
  title,
  body,
  tone = "neutral",
  action,
}: {
  title: string;
  body: ReactNode;
  tone?: "neutral" | "error" | "empty";
  action?: ReactNode;
}) {
  const ring =
    tone === "error"
      ? "border-neg/30 bg-neg-soft"
      : tone === "empty"
        ? "border-accent/30 bg-accent-soft/40"
        : "border-line bg-surface";
  return (
    <Card className={cn("p-8 text-center", ring)}>
      <h3 className="font-display text-lg font-semibold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-ink-muted">{body}</p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </Card>
  );
}
