import { useMemo, useState } from "react";
import { Card } from "../../ui/Card";
import { Skeleton } from "./states";
import { useVideos, type VideoRow } from "../../data/useVideos";
import { usd, compact, titleCase } from "../../lib/format";
import { cn } from "../../lib/cn";

type SortKey = "revenue_usd" | "views" | "rpm_usd";

export function VideoTable() {
  const { data, isLoading } = useVideos();
  const [sort, setSort] = useState<SortKey>("revenue_usd");
  const [dir, setDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const s = [...(data ?? [])].sort((a, b) => a[sort] - b[sort]);
    return dir === "desc" ? s.reverse() : s;
  }, [data, sort, dir]);

  const onSort = (key: SortKey) => {
    if (key === sort) setDir(dir === "desc" ? "asc" : "desc");
    else {
      setSort(key);
      setDir("desc");
    }
  };

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between p-6 pb-4">
        <h2 className="font-display text-lg font-semibold text-ink">Per-video profitability</h2>
        <span className="font-mono text-xs text-ink-subtle">Last 30 days</span>
      </div>

      {isLoading ? (
        <div className="space-y-2 px-6 pb-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-full" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <div className="px-6 pb-8 pt-2 text-center text-sm text-ink-muted">
          No videos with data in this window yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-y border-line bg-surface-alt text-left">
                <Th>Video</Th>
                <Th>Category</Th>
                <Th sortable active={sort === "views"} dir={dir} onClick={() => onSort("views")} align="right">
                  Views
                </Th>
                <Th sortable active={sort === "rpm_usd"} dir={dir} onClick={() => onSort("rpm_usd")} align="right">
                  RPM
                </Th>
                <Th
                  sortable
                  active={sort === "revenue_usd"}
                  dir={dir}
                  onClick={() => onSort("revenue_usd")}
                  align="right"
                >
                  Revenue
                </Th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((v: VideoRow) => (
                <tr key={v.id} className="border-b border-line last:border-0 hover:bg-surface-alt">
                  <td className="max-w-[260px] truncate px-6 py-3 font-medium text-ink">{v.title}</td>
                  <td className="px-6 py-3">
                    <span className="rounded-sm bg-ink/[0.05] px-2 py-0.5 font-mono text-[11px] text-ink-muted">
                      {titleCase(v.category)}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-ink-muted tnum">
                    {compact(v.views)}
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-ink-muted tnum">
                    ${v.rpm_usd.toFixed(1)}
                  </td>
                  <td className="px-6 py-3 text-right font-mono font-semibold text-ink tnum">
                    {usd(v.revenue_usd, { cents: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function Th({
  children,
  sortable,
  active,
  dir,
  onClick,
  align = "left",
}: {
  children: React.ReactNode;
  sortable?: boolean;
  active?: boolean;
  dir?: "asc" | "desc";
  onClick?: () => void;
  align?: "left" | "right";
}) {
  return (
    <th
      className={cn(
        "px-6 py-2.5 font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-subtle",
        align === "right" && "text-right",
      )}
    >
      {sortable ? (
        <button
          onClick={onClick}
          className={cn(
            "inline-flex items-center gap-1 hover:text-ink",
            active && "text-ink",
            align === "right" && "flex-row-reverse",
          )}
        >
          {children}
          <span aria-hidden className="text-[9px]">
            {active ? (dir === "desc" ? "▼" : "▲") : "↕"}
          </span>
        </button>
      ) : (
        children
      )}
    </th>
  );
}
