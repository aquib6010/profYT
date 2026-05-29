import { Topbar } from "../components/dashboard/Topbar";
import { StatCards } from "../components/dashboard/StatCards";
import { RevenuePanel } from "../components/dashboard/RevenuePanel";
import { AnomalyFeed } from "../components/dashboard/AnomalyFeed";
import { RecommendationsPanel } from "../components/dashboard/RecommendationsPanel";
import { VideoTable } from "../components/dashboard/VideoTable";
import { StatCardsSkeleton, Skeleton, PanelMessage } from "../components/dashboard/states";
import { ButtonLink } from "../ui/Button";
import { useAuth, loginUrl } from "../auth/useAuth";
import { useSummary } from "../auth/useSummary";

export default function Dashboard() {
  const { creator } = useAuth();
  const { data, isLoading, isError } = useSummary();

  return (
    <div className="min-h-screen bg-paper">
      <Topbar />
      <main className="mx-auto max-w-app px-6 py-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-display-md font-bold text-ink">
              {creator?.display_name ? `${creator.display_name}'s channel` : "Dashboard"}
            </h1>
            <p className="mt-1 text-sm text-ink-muted">
              Revenue intelligence
              {data?.as_of && (
                <>
                  {" "}
                  · last 30 days through <span className="font-mono tnum">{data.as_of}</span>
                </>
              )}
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-6">
          {isLoading && (
            <>
              <StatCardsSkeleton />
              <Skeleton className="h-[380px] w-full rounded-lg" />
            </>
          )}

          {isError && (
            <PanelMessage
              tone="error"
              title="Couldn't load your analytics"
              body="The API didn't respond. Make sure the backend is running, then retry."
            />
          )}

          {data && !data.has_data && (
            <>
              <StatCards data={data} />
              <PanelMessage
                tone="empty"
                title="No analytics for this channel yet"
                body="Once your videos are ingested, your revenue trend, alerts, and per-video profitability will appear here."
                action={
                  <ButtonLink href={loginUrl} variant="secondary" size="sm">
                    Reconnect channel
                  </ButtonLink>
                }
              />
            </>
          )}

          {data && data.has_data && (
            <>
              <StatCards data={data} />
              <RevenuePanel />
              <div className="grid gap-6 lg:grid-cols-2">
                <AnomalyFeed />
                <RecommendationsPanel />
              </div>
              <VideoTable />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
