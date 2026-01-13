export type OhlcvRow = [number, number, number, number, number, number];

export type TopGainerItem = {
  symbol: string;
  market_id?: string | null;
  base: string;
  quote: string;
  last: number | null;
  change_pct: number;
  ohlcv: OhlcvRow[];
};

export type TopGainersResponse = {
  exchange: string;
  market: "spot" | "swap";
  quote: string;
  timeframe: string;
  limit: number;
  top: number;
  updated_at: string;
  source: "live" | "cache";
  items: TopGainerItem[];
};

export async function fetchTopGainers(params: {
  exchange?: string;
  market?: "spot" | "swap";
  quote?: string;
  timeframe: string;
  limit: number;
  top: number;
  force?: boolean;
}): Promise<TopGainersResponse> {
  const url = new URL("/api/top-gainers", window.location.origin);
  url.searchParams.set("timeframe", params.timeframe);
  url.searchParams.set("limit", String(params.limit));
  url.searchParams.set("top", String(params.top));
  if (params.exchange) url.searchParams.set("exchange", params.exchange);
  if (params.market) url.searchParams.set("market", params.market);
  if (params.quote) url.searchParams.set("quote", params.quote);
  if (params.force) url.searchParams.set("force", "true");

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as TopGainersResponse;
}
