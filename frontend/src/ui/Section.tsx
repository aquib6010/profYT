import type { ReactNode } from "react";
import { cn } from "../lib/cn";
import { Container } from "./Container";

/** A marketing section with consistent vertical rhythm + optional eyebrow/heading. */
export function Section({
  id,
  eyebrow,
  title,
  intro,
  children,
  className,
  center = false,
}: {
  id?: string;
  eyebrow?: string;
  title?: ReactNode;
  intro?: ReactNode;
  children?: ReactNode;
  className?: string;
  center?: boolean;
}) {
  return (
    <section id={id} className={cn("py-20 sm:py-28", className)}>
      <Container>
        {(eyebrow || title || intro) && (
          <div className={cn("max-w-2xl", center && "mx-auto text-center")}>
            {eyebrow && (
              <div className="font-mono text-xs uppercase tracking-[0.18em] text-accent">
                {eyebrow}
              </div>
            )}
            {title && (
              <h2 className="mt-3 text-display-md font-semibold text-ink sm:text-display-lg">
                {title}
              </h2>
            )}
            {intro && <p className="mt-4 text-lg leading-relaxed text-ink-muted">{intro}</p>}
          </div>
        )}
        {children}
      </Container>
    </section>
  );
}
