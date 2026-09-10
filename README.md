# Royal Tyres IT Asset Request Tool

An internal IT asset request portal for Mohammed Farhaan Buckas's technical interview. The authoritative requirements are in [PROJECT_SPEC.md](PROJECT_SPEC.md).

React/Vite views call thin FastAPI controllers, which delegate to services and SQLAlchemy models. Local development uses SQLite. The hosted application uses Vercel for the frontend, Render for FastAPI, and Render PostgreSQL. Zendesk is a secondary integration; an outage must never discard a saved request.

## Local setup

Prerequisites: Python 3.13 and Node.js 22.12+ (Node 24 supported).

Backend (from `backend`):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --reload
```

On macOS/Linux use `.venv/bin/python` and `cp .env.example .env`. Set your own demo credentials in `.env`. Never commit this file.

Frontend (separate terminal, from `frontend`):

```sh
npm ci
# Copy .env.example to .env and configure VITE_API_URL.
npm run dev
```

Local API: `http://localhost:8000/health`. Swagger: `http://localhost:8000/docs`. Frontend: `http://localhost:5173`.

## Validation

From `backend`: `.venv\Scripts\python -m pytest`.
From `frontend`: `npm run build`.

## Environment

| Variable | Purpose |
| --- | --- |
| `APP_USERNAME`, `APP_PASSWORD` | Backend-only demo Basic Auth credentials |
| `DATABASE_URL` | Local SQLite or hosted Render PostgreSQL connection string |
| `FRONTEND_URL` | Allowed frontend origin, supplied through backend environment |
| `ZENDESK_SUBDOMAIN` | Authorised sandbox subdomain from the specification |
| `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` | Backend-only Zendesk API authentication |
| `ZENDESK_WEBHOOK_SECRET` | Backend-only shared secret for inbound webhooks |
| `VITE_API_URL` | Public API origin, the only frontend environment variable |

## Delivery sequence

The nine named branches and pull requests in specification Section 29 cover scaffold, core API, security, request UI, Zendesk creation, webhook/reconciliation, dashboard, deployment, and final documentation. Each starts from updated `main` and is tested and reviewed before merge.

This scaffold contains a running frontend, `/health`, and Swagger. Business endpoints and deployment configuration will arrive in their specified phases.
