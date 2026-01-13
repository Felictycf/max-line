from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import TopGainersResponse
from app.services.market_data import MarketDataService
from app.settings import Settings

settings = Settings()
service = MarketDataService(settings)

@asynccontextmanager
async def lifespan(_: FastAPI):
    service.start()
    yield
    await service.stop()


app = FastAPI(title="max-line API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/top-gainers", response_model=TopGainersResponse)
async def top_gainers(
    exchange: str = Query(default=settings.exchange),
    market: str = Query(default=settings.market, pattern="^(spot|swap)$"),
    quote: str = Query(default=settings.quote),
    timeframe: str = Query(default=settings.timeframe),
    limit: int = Query(default=settings.limit, ge=2, le=1000),
    top: int = Query(default=settings.top, ge=1, le=50),
    force: bool = Query(default=False),
) -> TopGainersResponse:
    try:
        return await service.get_top_gainers(
            exchange=exchange,
            market=market,
            quote=quote,
            timeframe=timeframe,
            limit=limit,
            top=top,
            force=force,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load market data: {type(e).__name__}") from e
