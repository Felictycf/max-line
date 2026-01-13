from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import ccxt.async_support as ccxt

from app.models import TopGainerItem, TopGainersResponse
from app.settings import Settings


@dataclass(frozen=True)
class RequestParams:
    exchange: str
    market: str
    quote: str
    timeframe: str
    limit: int
    top: int


class MarketDataService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()
        self._cache: dict[RequestParams, TopGainersResponse] = {}
        self._cache_ts: dict[RequestParams, float] = {}
        self._refresh_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._settings.auto_refresh or self._refresh_task is not None:
            return
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def stop(self) -> None:
        if self._refresh_task is None:
            return
        self._refresh_task.cancel()
        try:
            await self._refresh_task
        except asyncio.CancelledError:
            pass
        self._refresh_task = None

    async def get_top_gainers(
        self,
        *,
        exchange: str,
        market: str,
        quote: str,
        timeframe: str,
        limit: int,
        top: int,
        force: bool,
    ) -> TopGainersResponse:
        params = RequestParams(exchange=exchange, market=market, quote=quote, timeframe=timeframe, limit=limit, top=top)
        cached = await self._get_cache(params)
        if cached is not None and not force:
            return cached

        try:
            fresh = await self._fetch_live(params)
        except Exception:
            if cached is not None:
                return cached
            raise

        await self._set_cache(params, fresh)
        return fresh

    async def _get_cache(self, params: RequestParams) -> TopGainersResponse | None:
        async with self._lock:
            ts = self._cache_ts.get(params)
            if ts is None:
                return None
            age = asyncio.get_running_loop().time() - ts
            if age > self._settings.cache_ttl_seconds:
                return None
            cached = self._cache.get(params)
            if cached is None:
                return None
            return cached.model_copy(update={"source": "cache"})

    async def _set_cache(self, params: RequestParams, value: TopGainersResponse) -> None:
        async with self._lock:
            self._cache[params] = value
            self._cache_ts[params] = asyncio.get_running_loop().time()

    async def _refresh_loop(self) -> None:
        while True:
            try:
                await self.get_top_gainers(
                    exchange=self._settings.exchange,
                    market=self._settings.market,
                    quote=self._settings.quote,
                    timeframe=self._settings.timeframe,
                    limit=self._settings.limit,
                    top=self._settings.top,
                    force=True,
                )
            except Exception:
                pass
            await asyncio.sleep(self._settings.refresh_interval_seconds)

    async def _fetch_live(self, params: RequestParams) -> TopGainersResponse:
        exchange = self._make_exchange(params.exchange, market=params.market)
        try:
            await exchange.load_markets()
            candidates = self._select_candidates(exchange, quote=params.quote, market=params.market)
            tickers = await self._fetch_tickers(exchange, candidates)

            gainers: list[tuple[str, dict[str, Any], float]] = []
            for symbol in candidates:
                ticker = tickers.get(symbol)
                if not isinstance(ticker, dict):
                    continue
                change_pct = self._ticker_change_pct(ticker)
                if change_pct is None:
                    continue
                gainers.append((symbol, ticker, change_pct))

            gainers.sort(key=lambda x: x[2], reverse=True)
            top_slice = gainers[: params.top]

            semaphore = asyncio.Semaphore(6)

            async def load_item(symbol: str, ticker: dict[str, Any], change_pct: float) -> TopGainerItem:
                async with semaphore:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=params.timeframe, limit=params.limit)
                base, quote = symbol.split("/", 1)
                quote = quote.split(":", 1)[0]
                market_id: str | None = None
                try:
                    m = exchange.market(symbol)
                    market_id = m.get("id")
                    base = m.get("base") or base
                    quote = m.get("quote") or quote
                except Exception:
                    pass
                return TopGainerItem(
                    symbol=symbol,
                    market_id=market_id,
                    base=base,
                    quote=quote,
                    last=ticker.get("last"),
                    change_pct=change_pct,
                    ohlcv=[[float(row[0])] + [float(v) for v in row[1:]] for row in ohlcv],
                )

            results = await asyncio.gather(
                *(load_item(symbol, ticker, change_pct) for symbol, ticker, change_pct in top_slice),
                return_exceptions=True,
            )
            items: list[TopGainerItem] = []
            for res in results:
                if isinstance(res, Exception):
                    continue
                items.append(res)

            return TopGainersResponse(
                exchange=params.exchange,
                market="swap" if params.market == "swap" else "spot",
                quote=params.quote,
                timeframe=params.timeframe,
                limit=params.limit,
                top=params.top,
                updated_at=datetime.now(timezone.utc),
                source="live",
                items=items,
            )
        finally:
            await exchange.close()

    def _make_exchange(self, exchange_name: str, *, market: str) -> ccxt.Exchange:
        # Binance futures data should use the dedicated CCXT exchange ids to avoid mixed/incorrect markets.
        effective = exchange_name
        if exchange_name == "binance" and market == "swap":
            effective = "binanceusdm"

        if not hasattr(ccxt, effective):
            raise ValueError(f"Unsupported exchange: {effective}")

        exchange_class = getattr(ccxt, effective)
        exchange = exchange_class({"enableRateLimit": True})

        self._apply_proxy_from_env(exchange)
        return exchange

    def _apply_proxy_from_env(self, exchange: ccxt.Exchange) -> None:
        explicit = os.getenv("MAXLINE_PROXY_URL")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        all_proxy = os.getenv("ALL_PROXY") or os.getenv("all_proxy")

        proxy_url = explicit or https_proxy or http_proxy
        if proxy_url:
            if proxy_url.lower().startswith("socks"):
                if hasattr(exchange, "socksProxy"):
                    exchange.socksProxy = proxy_url
                elif hasattr(exchange, "socks_proxy"):
                    exchange.socks_proxy = proxy_url
                return

            # Avoid CCXT "conflicting proxy settings" by setting only one.
            if https_proxy or proxy_url.lower().startswith("https"):
                if hasattr(exchange, "httpsProxy"):
                    exchange.httpsProxy = proxy_url
                elif hasattr(exchange, "https_proxy"):
                    exchange.https_proxy = proxy_url
                return

            if hasattr(exchange, "httpProxy"):
                exchange.httpProxy = proxy_url
            elif hasattr(exchange, "http_proxy"):
                exchange.http_proxy = proxy_url
            return

        if all_proxy and all_proxy.lower().startswith("socks"):
            for attr in ("socksProxy", "socks_proxy"):
                if hasattr(exchange, attr):
                    setattr(exchange, attr, all_proxy)

    async def _fetch_tickers(self, exchange: ccxt.Exchange, symbols: list[str]) -> dict[str, Any]:
        has = getattr(exchange, "has", {}) or {}
        if has.get("fetchTickers"):
            # Some exchanges accept a list of symbols, which keeps results consistent with loaded markets.
            try:
                return await exchange.fetch_tickers(symbols)
            except Exception:
                return await exchange.fetch_tickers()
        out: dict[str, Any] = {}
        if not has.get("fetchTicker"):
            return out

        semaphore = asyncio.Semaphore(6)

        async def load(symbol: str) -> None:
            async with semaphore:
                out[symbol] = await exchange.fetch_ticker(symbol)

        await asyncio.gather(*(load(symbol) for symbol in symbols), return_exceptions=True)
        return out

    def _select_candidates(self, exchange: ccxt.Exchange, *, quote: str, market: str) -> list[str]:
        out: list[str] = []
        markets = getattr(exchange, "markets", {}) or {}
        for symbol, m in markets.items():
            if not isinstance(m, dict):
                continue
            if not m.get("active", True):
                continue

            if market == "spot":
                if not m.get("spot"):
                    continue
                if m.get("quote") != quote:
                    continue
            else:
                if not m.get("swap"):
                    continue
                if m.get("quote") != quote:
                    continue
                settle = m.get("settle")
                if settle and settle != quote:
                    continue
                if m.get("linear") is False:
                    continue
                info = m.get("info") or {}
                if isinstance(info, dict):
                    contract_type = info.get("contractType")
                    if contract_type and contract_type != "PERPETUAL":
                        continue
                    status = info.get("status")
                    if status and status != "TRADING":
                        continue

            base = m.get("base") or symbol.split("/", 1)[0]
            if not base:
                continue
            if len(base) < 2:
                continue
            if base.isdigit():
                continue
            if base.endswith(("UP", "DOWN", "BULL", "BEAR")):
                continue

            out.append(symbol)

        return out

    def _ticker_change_pct(self, ticker: dict[str, Any]) -> float | None:
        pct = ticker.get("percentage")
        if isinstance(pct, (int, float)):
            return float(pct)
        last = ticker.get("last")
        open_ = ticker.get("open")
        if isinstance(last, (int, float)) and isinstance(open_, (int, float)) and open_ != 0:
            return (float(last) - float(open_)) / float(open_) * 100.0
        return None
