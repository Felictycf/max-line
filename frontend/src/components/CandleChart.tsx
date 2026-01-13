import { createChart, ColorType, IChartApi, ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import React, { useEffect, useMemo, useRef } from "react";
import type { OhlcvRow } from "../api";

type Props = {
  ohlcv: OhlcvRow[];
};

function toSeriesData(ohlcv: OhlcvRow[]) {
  return ohlcv.map((row) => ({
    time: Math.floor(row[0] / 1000) as UTCTimestamp,
    open: row[1],
    high: row[2],
    low: row[3],
    close: row[4]
  }));
}

export default function CandleChart({ ohlcv }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  const data = useMemo(() => toSeriesData(ohlcv), [ohlcv]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: Math.max(80, el.clientHeight || 220),
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#c9d1d9"
      },
      grid: {
        horzLines: { color: "rgba(255,255,255,0.06)" },
        vertLines: { color: "rgba(255,255,255,0.06)" }
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
      timeScale: { borderColor: "rgba(255,255,255,0.1)" }
    });
    const series = chart.addCandlestickSeries({
      upColor: "#2ea043",
      downColor: "#f85149",
      borderVisible: false,
      wickUpColor: "#2ea043",
      wickDownColor: "#f85149"
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: el.clientWidth, height: Math.max(80, el.clientHeight || 220) });
      chart.timeScale().fitContent();
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    series.setData(data);
    chart.timeScale().fitContent();
  }, [data]);

  return <div ref={containerRef} className="chart" />;
}
