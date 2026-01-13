from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAXLINE_", env_file=".env", extra="ignore")

    exchange: str = "binance"
    market: str = "spot"
    quote: str = "USDT"
    timeframe: str = "1m"
    limit: int = 120
    top: int = 12

    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    cache_ttl_seconds: int = 20
    auto_refresh: bool = True
    refresh_interval_seconds: int = 30
