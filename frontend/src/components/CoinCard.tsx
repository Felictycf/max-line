import React from "react";
import type { TopGainerItem } from "../api";
import CandleChart from "./CandleChart";

function formatPct(pct: number) {
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

export default function CoinCard({ item }: { item: TopGainerItem }) {
  const isUp = item.change_pct >= 0;
  return (
    <div className="card">
      <div className="cardHeader">
        <div className="symbol">
          {item.market_id ?? item.symbol}
          {item.market_id ? <span className="symbolAlt">{item.symbol}</span> : null}
        </div>
        <div className={isUp ? "pct up" : "pct down"}>{formatPct(item.change_pct)}</div>
      </div>
      <div className="sub">
        <div className="muted">Last</div>
        <div className="value">{item.last ?? "—"}</div>
      </div>
      <CandleChart ohlcv={item.ohlcv} />
    </div>
  );
}
