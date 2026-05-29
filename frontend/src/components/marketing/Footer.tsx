import { Container } from "../../ui/Container";
import { Logo } from "../../ui/Logo";

const cols = [
  { title: "Product", links: ["Features", "How it works", "Pricing", "FAQ"] },
  { title: "Company", links: ["About", "Blog", "Careers", "Contact"] },
  { title: "Legal", links: ["Privacy", "Terms", "Data policy", "Security"] },
];

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface-alt">
      <Container className="py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_repeat(3,1fr)]">
          <div className="max-w-xs">
            <Logo />
            <p className="mt-3 text-sm text-ink-muted">
              Revenue intelligence for YouTube creators.
            </p>
          </div>
          {cols.map((c) => (
            <div key={c.title}>
              <div className="font-mono text-xs uppercase tracking-[0.12em] text-ink-subtle">
                {c.title}
              </div>
              <ul className="mt-4 space-y-2.5">
                {c.links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-sm text-ink-muted hover:text-ink">
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-line pt-6 sm:flex-row">
          <p className="font-mono text-xs text-ink-subtle">
            © {new Date().getFullYear()} Profitly · Revenue intelligence for YouTube creators
          </p>
          <div className="flex gap-4 text-sm text-ink-muted">
            <a href="#" className="hover:text-ink">
              X
            </a>
            <a href="#" className="hover:text-ink">
              GitHub
            </a>
            <a href="#" className="hover:text-ink">
              LinkedIn
            </a>
          </div>
        </div>
      </Container>
    </footer>
  );
}
