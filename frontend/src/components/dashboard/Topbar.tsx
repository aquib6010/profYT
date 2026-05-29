import { Link } from "react-router-dom";
import { Logo } from "../../ui/Logo";
import { Button } from "../../ui/Button";
import { useAuth, useLogout } from "../../auth/useAuth";

export function Topbar() {
  const { creator } = useAuth();
  const logout = useLogout();

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-app items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link to="/" aria-label="Profitly home">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-6 sm:flex">
            <span className="text-sm font-medium text-ink">Dashboard</span>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {creator && (
            <span className="hidden font-mono text-xs text-ink-muted sm:inline">
              {creator.email}
            </span>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            {logout.isPending ? "Signing out…" : "Sign out"}
          </Button>
        </div>
      </div>
    </header>
  );
}
