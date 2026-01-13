.PHONY: dev-backend dev-frontend

dev-backend:
\tuvicorn app.main:app --reload --app-dir backend --host 0.0.0.0 --port 8010

dev-frontend:
\tnpm --prefix frontend run dev -- --host 0.0.0.0 --port 5174
