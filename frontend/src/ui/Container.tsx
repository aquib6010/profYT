import type { ReactNode } from "react";
import { cn } from "../lib/cn";

/** Centered max-width wrapper. `wide` uses the dashboard width (1280px). */
export function Container({
  children,
  className,
  wide = false,
}: {
  children: ReactNode;
  className?: string;
  wide?: boolean;
}) {
  return (
    <div className={cn("mx-auto w-full px-6", wide ? "max-w-app" : "max-w-[1200px]", className)}>
      {children}
    </div>
  );
}
