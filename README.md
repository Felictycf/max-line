# max-line

FastAPI + CCXT 后端，React 前端，用于展示涨幅前 12 的币种与 K 线图。

## 目录

- `backend/`: FastAPI API 服务（通过 CCXT 拉取交易所数据）
- `frontend/`: React 仪表盘（展示榜单与 K 线图）

## 开发运行

复制环境变量（可选）：

```bash
cp .env.example .env
```

### 后端

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

后端默认地址：`http://localhost:8000`
（如果 8000 端口被占用，可改用 `http://localhost:8010`）

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://localhost:5173`（已将 `/api` 代理到后端）
（如果 5173 端口被占用，可改用 `http://localhost:5174`）

## API

- `GET /api/health`
- `GET /api/top-gainers?exchange=binance&market=spot&quote=USDT&timeframe=1m&limit=120&top=12`
- `GET /api/top-gainers?exchange=binance&market=swap&quote=USDT&timeframe=1m&limit=120&top=12`

可选参数：

- `force=true`：强制刷新（忽略缓存）
