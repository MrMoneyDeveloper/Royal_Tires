# Royal Tyres IT Asset Request Tool

An internal IT asset request portal for Mohammed Farhaan Buckas's Royal Tyres technical interview. The authoritative architecture and implementation notes are in [PROJECT_SPEC.md](PROJECT_SPEC.md).

React/Vite views call thin FastAPI controllers, which delegate to services, repositories and SQLAlchemy models. Local development uses SQLite. The hosted application uses Vercel for the frontend, Render for FastAPI, Render PostgreSQL for persistence, and a Zendesk sandbox as the helpdesk integration.

The local SQL request is committed before any Zendesk call. A Zendesk outage therefore cannot discard an employee request.

## User-facing views

The portal now has three clear operational views:

- **New request**: submit an IT asset request.
- **Request queue**: see incoming requests, local status, linked Zendesk ticket, Zendesk status and sync health.
- **Track a request**: inspect one request in detail and see the Portal → Zendesk → webhook status-sync path.

The Zendesk Setup view is separate from normal request handling and clearly distinguishes project-owned configuration from pre-existing sandbox rules.

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

Business Reason validation is enforced independently on the frontend and backend. Whitespace, tabs and newline characters do not count toward the minimum 10 meaningful characters.

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
| `ZENDESK_LEGACY_TRIGGER_GUARD_ENABLED` | Opt-in guard for the seven confirmed pre-existing sandbox triggers that must ignore Royal Tyres |
| `RENDER_EXTERNAL_URL` | Render-provided public backend origin used for the webhook callback |
| `VITE_API_URL` | Public API origin; frontend environment value |

Zendesk credentials and webhook secrets never enter the React application.

## Governed Zendesk setup

The Zendesk Setup page follows this flow:

```text
Test backend ENV credentials
→ discover current Zendesk state
→ show CREATE / REUSE / UPDATE / SKIP plan
→ fingerprint the exact plan
→ explicit human approval
→ re-read and reject drift
→ apply approved changes only
→ read everything back
→ verify PASS / FAIL
```

The project-owned plan covers:

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

The setup page also has an **Existing sandbox safeguards** section. When the opt-in guard is enabled, only the seven confirmed legacy triggers are eligible for UPDATE. The permitted edit is one additional ALL condition:

```text
Brand IS NOT Royal Tyres
```

Their existing titles, active states, actions and other conditions are preserved and verified after the update. Unrelated Zendesk configuration is not deleted. Existing exact project-owned resources are reused, so a partially failed deployment can be retried safely.

## Live workflow

```text
Employee submits request
→ PostgreSQL commit
→ Zendesk ticket created
→ demo notification email
→ request appears in Request queue
→ agent changes Zendesk status
→ Zendesk trigger calls authenticated FastAPI webhook
→ PostgreSQL status updated
→ Request queue / Track a Request show the new status
```

The tracking page refreshes its local API data every 10 seconds while open and provides a manual **Refresh status** button. The browser never calls Zendesk directly.

## Pull request progression

PR1–PR4 cover scaffold, core API, security and request UI. PR5 added governed Zendesk setup and ticket creation. PR6 corrected live Zendesk API field/view values. PR7 added email notifications, webhook status callbacks and tracking-page synchronization. PR8 expanded the MVC architecture map. PR9 improved safe Zendesk validation diagnostics. PR10 fixed cross-field Zendesk option-tag collisions. PR11 added opt-in isolation for the confirmed legacy sandbox triggers. PR12 fixed meaningful Business Reason validation. The request queue and setup-clarity work continues in the next focused UI PR.
