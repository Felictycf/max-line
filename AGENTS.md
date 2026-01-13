# max-line - Agent Development Guide

## Project Overview
FastAPI + CCXT backend (Python) and React dashboard (TypeScript + Vite) for displaying top crypto gainers with candlestick charts.

---

## Build & Run Commands

### Backend (Python)
```bash
source .venv/bin/activate && pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend --host 0.0.0.0 --port 8010
# Or: make dev-backend
```

### Frontend (React + TypeScript)
```bash
cd frontend && npm install
npm run dev    # port 5173, proxies /api to backend (or: make dev-frontend)
npm run build   # tsc -b && vite build
npm run preview
```

### Testing
**No test framework is configured.** No test commands available.

---

## Code Style Guidelines

### Python (Backend)
```python
from __future__ import annotations  # REQUIRED - modern type hints

# Imports: stdlib → third-party → local
from contextlib import asynccontextmanager
from typing import Any
import ccxt.async_support as ccxt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Modern PEP 604 type syntax - REQUIRED
symbol: str | None      # NOT: Optional[str]
items: list[TopGainerItem]  # NOT: List[TopGainerItem]

# Async/await pattern - all I/O must be async
async def get_data() -> dict[str, Any]: ...

# Pydantic models for API validation
class TopGainerItem(BaseModel):
    symbol: str
    change_pct: float = Field(..., description="...")
    meta: dict[str, Any] = Field(default_factory=dict)

# Error handling: HTTPException with status codes
raise HTTPException(status_code=400, detail=str(e)) from e
```

**Naming**: `snake_case` for vars/functions, `PascalCase` for classes, `_private` for private members.  
**Async patterns**: `asynccontextmanager` for cleanup, `asyncio.Lock` for shared state, `asyncio.gather(*coros, return_exceptions=True)` for parallel ops, `asyncio.Semaphore` for rate limiting (default: 6 concurrent).

**Dependencies**: FastAPI 0.115.6, CCXT 4.5.30, Pydantic Settings, cachetools.

---

### TypeScript (Frontend)
```typescript
// Imports: external → local (type-only for types)
import React, { useEffect, useMemo, useRef, useState } from "react";
import type { TopGainerItem } from "./api";
import CoinCard from "./components/CoinCard";

// Type aliases for complex types
export type OhlcvRow = [number, number, number, number, number, number];
export type TopGainerItem = {
  symbol: string;
  market_id?: string | null;
  change_pct: number;
  ohlcv: OhlcvRow[];
};

// Functional components with hooks only (no classes)
export default function App() {
  const [data, setData] = useState<TopGainersResponse | null>(null);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let mounted = true;
    return () => { mounted = false; /* cleanup */ };
  }, [deps]);

  const formatted = useMemo(() => formatData(data), [data]);

  return <div ref={ref}>{/* ... */}</div>;
}
```

**Naming**: `PascalCase` for components/types, `camelCase` for vars/functions (prefer `type` over `interface`).  
**Error handling**: State-based `useState<string | null>`, conditional rendering `{error && <div className="error">{error}</div>}`.  
**Styling**: Plain CSS modules with semantic class names, CSS variables in `:root`, `@media` for responsive breakpoints, semantic HTML (`<button>`, `<label>`, `<select>`).

**TypeScript config**: `strict: true`, `target: ES2022`, `jsx: react-jsx`.  
**Dependencies**: React 18.3.1, lightweight-charts 4.2.0, Vite 5.4.10, TypeScript 5.6.3.

---

## Project Structure
```
max-line/
├── backend/app/
│   ├── main.py              # FastAPI app + routes
│   ├── models.py            # Pydantic models
│   ├── settings.py          # Config
│   └── services/
│       └── market_data.py   # CCXT integration
├── frontend/src/
│   ├── api.ts              # API client + types
│   ├── App.tsx             # Main component
│   ├── styles.css          # Global styles
│   └── components/
│       ├── CoinCard.tsx
│       └── CandleChart.tsx
└── Makefile               # Quick dev commands
```

## Key Patterns
- **Backend**: FastAPI async/await, Pydantic models, CCXT for exchange data, custom asyncio caching with locks
- **Frontend**: React hooks, TypeScript strict mode, functional components, lightweight-charts for visualization
- **API**: `/api/health`, `/api/top-gainers` (RESTful), CORS enabled, Vite proxy
- **No tests**: Manual testing required

## Environment
- Backend: Python 3.x, port 8010 (or 8000)
- Frontend: port 5173 (or 5174), proxies `/api` to backend
- Config: `.env.example` available
