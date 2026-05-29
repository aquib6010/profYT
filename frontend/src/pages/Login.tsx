import { Link, Navigate, useSearchParams } from "react-router-dom";
import { Logo } from "../ui/Logo";
import { ButtonLink } from "../ui/Button";
import { Card } from "../ui/Card";
import { useAuth, loginUrl } from "../auth/useAuth";

// Map the backend's ?error= codes (api/auth.py) to human-readable text.
function errorMessage(code: string): string {
  if (code === "access_denied")
    return "You declined the permission request. Approve access to sign in.";
  if (code === "no_youtube_channel")
    return "That Google account has no YouTube channel. Sign in with the account that owns your channel.";
  if (code === "token_exchange_failed")
    return "Couldn't complete sign-in with Google. Please try again.";
  if (code === "userinfo_incomplete")
    return "Google didn't return your account details. Please try again.";
  if (code.startsWith("youtube_api_"))
    return "YouTube API request failed. Make sure the YouTube Data & Analytics APIs are enabled.";
  if (code.startsWith("userinfo_")) return "Couldn't read your Google profile. Please try again.";
  return `Sign-in failed (${code}).`;
}

export default function Login() {
  const { isAuthenticated, isLoading } = useAuth();
  const [params] = useSearchParams();
  const error = params.get("error");

  if (!isLoading && isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="flex min-h-screen flex-col bg-paper bg-ledger">
      <header className="px-6 py-5">
        <Link to="/" aria-label="Profitly home">
          <Logo />
        </Link>
      </header>

      <main className="flex flex-1 items-center justify-center px-6 pb-20">
        <Card className="w-full max-w-md p-8 shadow-lg">
          <div className="font-mono text-xs uppercase tracking-[0.18em] text-accent">
            Welcome back
          </div>
          <h1 className="mt-3 text-display-sm font-semibold text-ink">Sign in to Profitly</h1>
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">
            Connect your YouTube channel to see per-video revenue, earnings forecasts, and
            content-mix recommendations.
          </p>

          {error && (
            <div
              role="alert"
              className="mt-5 rounded-md border border-neg/30 bg-neg-soft px-3 py-2.5 text-sm text-neg"
            >
              {errorMessage(error)}
            </div>
          )}

          <ButtonLink href={loginUrl} size="lg" className="mt-6 w-full">
            Continue with Google
          </ButtonLink>

          <p className="mt-4 font-mono text-[11px] leading-relaxed text-ink-subtle">
            Read-only access to your YouTube Analytics & revenue. Tokens encrypted at rest.
          </p>
        </Card>
      </main>
    </div>
  );
}
