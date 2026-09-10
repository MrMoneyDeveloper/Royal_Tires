# Royal Tyres IT Asset Request Tool

An internal IT asset request portal for Mohammed Farhaan Buckas's Royal Tyres technical interview. The authoritative implementation notes are in [PROJECT_SPEC.md](PROJECT_SPEC.md).

React/Vite views call thin FastAPI controllers, which delegate to services and SQLAlchemy models. Local development uses SQLite. The hosted application uses Vercel for the frontend, Render for FastAPI, Render PostgreSQL for persistence, and a Zendesk sandbox as the helpdesk integration.

The local SQL request is committed before any Zendesk call. A Zendesk outage therefore cannot discard an employee request.

## Local setup

Prerequisites: Python 3.13 and Node.js 22.12+.

Backend, from `backend`:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Frontend, from `frontend`:

```sh
npm ci
# Copy .env.example to .env and configure VITE_API_URL.
npm run dev
```

Local API: `http://localhost:8000/health`  
Swagger: `http://localhost:8000/docs`  
Frontend: `http://localhost:5173`

## Validation

Backend:

```text
python -m pytest
```

Frontend:

```text
npm test
npm run build
npm run test:e2e
```

GitHub Actions runs the backend suite, frontend unit tests, Vite production build and Playwright Chromium tests on pull requests and `main`.

## Environment

| Variable | Purpose |
| --- | --- |
| `APP_USERNAME`, `APP_PASSWORD` | Backend-only demo Basic Auth credentials |
| `DATABASE_URL` | SQLite locally or Render PostgreSQL hosted |
| `FRONTEND_URL` | Explicit allowed frontend origin(s) |
| `ZENDESK_SUBDOMAIN` | Backend-only Zendesk sandbox subdomain |
| `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` | Backend-only Zendesk API authentication |
| `ZENDESK_WEBHOOK_SECRET` | Separate bearer secret for Zendesk → FastAPI status callbacks |
| `ZENDESK_NOTIFICATION_EMAIL` | Demo email receiver; defaults to `farhaanhotd1@gmail.com` |
| `RENDER_EXTERNAL_URL` | Render-provided public backend origin used for the webhook callback |
| `VITE_API_URL` | Public API origin; frontend environment value |

Zendesk credentials and webhook secrets never enter the React application.

## Governed Zendesk setup

The Zendesk Setup page follows this flow:

```text
Test backend ENV credentials
→ discover current Zendesk state
→ show CREATE / REUSE plan
→ fingerprint exact plan
→ explicit human approval
→ re-read and reject drift
→ apply missing resources
→ verify all resources
```

The approved plan covers:

- Brand: `Royal Tyres`
- Group: `Royal Tyres | IT Service Desk`
- three Royal Tyres ticket fields
- Ticket Form: `Royal Tyres | IT Asset Request`
- View: `Royal Tyres | IT Asset Requests`
- Email Target: `Royal Tyres | Demo Notifications`
- Webhook: `Royal Tyres | Asset Status Sync`
- new-request email Trigger
- status-change email Trigger
- status-change portal-sync Trigger

No unrelated Zendesk configuration is deleted. Existing exact resources are reused, so a partially failed deployment can be retried safely.

## Live workflow

```text
Employee submits request
→ PostgreSQL commit
→ Zendesk ticket created
→ demo notification email
→ agent changes Zendesk status
→ Zendesk trigger calls authenticated FastAPI webhook
→ PostgreSQL status updated
→ Track a Request reflects the new status
```

The tracking page also refreshes its local API data every 10 seconds while open and provides a manual **Refresh status** button.

## Pull request progression

PR1–PR4 cover scaffold, core API, security and request UI. PR5 added governed Zendesk setup and ticket creation. PR6 corrected live Zendesk API field/view values. PR7 adds email notifications, webhook status callbacks and tracking-page synchronization.
