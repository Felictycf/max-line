from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TopGainerItem(BaseModel):
    symbol: str
    market_id: str | None = None
    base: str
    quote: str
    last: float | None = None
    change_pct: float = Field(..., description="Percent change over the most recent close-to-close interval.")
    ohlcv: list[list[float]] = Field(
        default_factory=list,
        description="CCXT OHLCV arrays: [timestamp_ms, open, high, low, close, volume]",
    )
    meta: dict[str, Any] = Field(default_factory=dict)


class TopGainersResponse(BaseModel):
    exchange: str
    market: Literal["spot", "swap"] = "spot"
    quote: str
    timeframe: str
    limit: int
    top: int
    updated_at: datetime
    source: Literal["live", "cache"] = "live"
    items: list[TopGainerItem]
