import type { ReactNode } from "react";
import { cn } from "../lib/cn";

/** Surface container — the base for every panel/card in the app. */
export function Card({
  children,
  className,
  interactive = false,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-line bg-surface shadow-sm",
        interactive && "transition-shadow hover:shadow-md",
        className,
      )}
    >
      {children}
    </div>
  );
}
