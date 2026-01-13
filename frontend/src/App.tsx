import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { fetchTopGainers, type TopGainersResponse } from "./api";
import CoinCard from "./components/CoinCard";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"] as const;

function preferredCols(n: number) {
  if (n <= 0) return 1;
  if (n <= 15) return Math.min(5, Math.max(1, Math.ceil(n / 3)));
  if (n <= 20) return 4;
  if (n <= 30) return 5;
  return 6;
}

export default function App() {
  const [market, setMarket] = useState<"spot" | "swap">("spot");
  const [timeframe, setTimeframe] = useState<(typeof TIMEFRAMES)[number]>("1m");
  const [limit, setLimit] = useState(120);
  const [top, setTop] = useState(12);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const [dataByMarket, setDataByMarket] = useState<{ spot: TopGainersResponse | null; swap: TopGainersResponse | null }>(
    { spot: null, swap: null }
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const gridRef = useRef<HTMLDivElement | null>(null);
  const [grid, setGrid] = useState({ cols: 3, rows: 1 });

  const data = dataByMarket[market];

  const title = useMemo(() => {
    const updated = data ? new Date(data.updated_at).toLocaleTimeString() : "—";
    const marketLabel = market === "spot" ? "现货" : "合约";
    return `Top ${top} gainers · ${marketLabel} · ${timeframe} · updated ${updated} (${data?.source ?? "—"})`;
  }, [data, timeframe, top, market]);

  useLayoutEffect(() => {
    const el = gridRef.current;
    if (!el) return;

    const n = Math.max(1, data?.items?.length ?? top);
    const minCellHeight = 180;

    const compute = () => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      const maxColsByWidth = Math.max(1, Math.min(n, Math.floor(w / 260)));

      let cols = Math.min(preferredCols(n), maxColsByWidth);
      cols = Math.max(1, cols);
      let rows = Math.ceil(n / cols);

      if (h > 0) {
        while (cols < maxColsByWidth && h / rows < minCellHeight) {
          cols += 1;
          rows = Math.ceil(n / cols);
        }
      }

      setGrid({ cols, rows });
    };

    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    window.addEventListener("resize", compute);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", compute);
    };
  }, [data?.items?.length, top]);

  useEffect(() => {
    let mounted = true;
    let timer: number | undefined;

    async function load(force = false) {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchTopGainers({ market, timeframe, limit, top, force });
        if (mounted) setDataByMarket((prev) => ({ ...prev, [market]: res }));
      } catch (e) {
        if (mounted) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void load(true);
    timer = window.setInterval(() => void load(false), 30_000);

    return () => {
      mounted = false;
      if (timer) window.clearInterval(timer);
    };
  }, [market, timeframe, limit, top, refreshNonce]);

  return (
    <div className="page">
      <header className="header">
        <div>
          <div className="brand">max-line</div>
          <div className="title">{title}</div>
        </div>
        <div className="controls">
          <div className="seg">
            <button className={market === "spot" ? "segBtn active" : "segBtn"} onClick={() => setMarket("spot")}>
              现货
            </button>
            <button className={market === "swap" ? "segBtn active" : "segBtn"} onClick={() => setMarket("swap")}>
              合约
            </button>
          </div>
          <label>
            Timeframe
            <select value={timeframe} onChange={(e) => setTimeframe(e.target.value as any)}>
              {TIMEFRAMES.map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </label>
          <label>
            Candles
            <input
              type="number"
              min={20}
              max={300}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </label>
          <label>
            Top
            <input type="number" min={1} max={24} value={top} onChange={(e) => setTop(Number(e.target.value))} />
          </label>
          <button className="btn" onClick={() => setRefreshNonce((n) => n + 1)} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      {error ? <div className="error">Backend error: {error}</div> : null}
      {loading && !data ? <div className="loading">Loading…</div> : null}

      <main className="grid">
        <div
          ref={gridRef}
          className="gridInner"
          style={
            {
              ["--cols" as any]: String(grid.cols),
              ["--rows" as any]: String(grid.rows)
            } as React.CSSProperties
          }
        >
          {(data?.items ?? []).map((item) => (
            <CoinCard key={item.symbol} item={item} />
          ))}
        </div>
      </main>
    </div>
  );
}
