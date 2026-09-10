# IT Asset Request Tool — Technical Interview Project Specification

**Candidate:** Mohammed Farhaan Buckas  
**Purpose:** Royal Tyres technical interview practical  
**Project type:** Small full-stack internal IT asset request application  
**Target demo:** Hosted and working end to end  
**Primary design goal:** Keep the code simple enough to explain file by file while still showing good technical judgement.

---

## 1. Project Summary

Build a small **IT Asset Request Tool** where a logged-in internal user can request an IT asset such as a laptop, mouse, keyboard, monitor, headset, or other approved item.

The application must:

1. Provide a frontend form with validation.
2. Submit the request to a backend API.
3. Store the request in SQL.
4. protect the API with simple Basic Authentication.
5. validate and safely handle user input.
6. log every important request/action.
7. create a ticket in a Zendesk sandbox.
8. store the returned Zendesk ticket ID.
9. receive status updates back from Zendesk through a webhook.
10. allow a manual Zendesk sync as a fallback.
11. provide an operational dashboard showing request usage and sync health.
12. expose Swagger/OpenAPI documentation.
13. be stored in GitHub.
14. be deployable with:
   - **Frontend:** Vercel
   - **Backend:** Render
   - **Database:** PostgreSQL for hosted demo
   - **Local development:** SQLite is acceptable

This is intentionally a **small monolithic application**, not a microservice system.

---

# 2. Why This Design

The exercise asks for a simple IT Asset Request Tool.

The architecture should therefore remain deliberately understandable.

The design demonstrates:

- frontend development
- backend API development
- MVC-style separation
- SQL persistence
- validation
- authentication
- REST API design
- logging
- Zendesk integration
- webhooks
- error handling
- Git/GitHub workflow
- Swagger/OpenAPI
- reporting/dashboard design
- basic operational monitoring

The project should **not** become unnecessarily complex.

Do not add:

- Kubernetes
- Redis
- message queues
- Docker unless deployment genuinely requires it
- Terraform
- OAuth provider integration
- multiple microservices
- event buses
- background workers unless absolutely necessary

The goal is to show sound engineering judgement, not framework collecting.

---

# 3. Interview Requirement Mapping

| Interview Requirement | Implementation |
|---|---|
| Frontend form | React + Vite |
| Validation | React validation + Pydantic backend validation |
| API endpoint | FastAPI |
| SQL / JSON persistence | SQLAlchemy + SQLite locally / PostgreSQL hosted |
| SQL injection protection | SQLAlchemy parameterised queries |
| XSS protection | React escaped rendering; no raw HTML injection |
| Basic Auth | FastAPI HTTP Basic using environment variables |
| Logging | Python application logging + audit log table |
| GitHub | Repository with commits and pull request workflow |
| Technical review | Swagger, live application, database records, dashboard |
| Helpdesk simulation | Real Zendesk sandbox integration |
| Monitoring | Dashboard sync/status information |

---

# 4. High-Level Architecture

```text
┌────────────────────────────┐
│        React + Vite        │
│          Vercel            │
│                            │
│  Request Form              │
│  Request Detail            │
│  Dashboard                 │
└──────────────┬─────────────┘
               │
               │ HTTPS / JSON
               ▼
┌────────────────────────────┐
│          FastAPI           │
│           Render           │
│                            │
│  Controllers               │
│  Validation                │
│  Basic Auth                │
│  Services                  │
│  Logging                   │
└───────┬──────────┬─────────┘
        │          │
        │          │
        ▼          ▼
┌─────────────┐   ┌───────────────┐
│ PostgreSQL  │   │ Zendesk       │
│             │   │ Sandbox       │
│ Requests    │   │               │
│ Audit Logs  │   │ IT Tickets    │
└──────┬──────┘   └───────┬───────┘
       │                  │
       │                  │ Webhook
       │                  ▼
       │          POST /api/webhooks/zendesk
       │                  │
       └──────────────────┘
```

---

# 5. MVC Mapping

The project should follow a simple MVC-style structure because the interview team works with MVC concepts.

### Model

The **Model** represents persisted application data.

Examples:

- AssetRequest
- AuditLog

Technology:

- SQLAlchemy
- SQLite locally
- PostgreSQL when hosted

### View

The **View** is the React frontend.

Examples:

- Asset Request Form
- Request Detail / Tracking View
- Dashboard

Technology:

- React
- Vite

### Controller

The **Controller** is the FastAPI API layer.

Controllers:

- receive HTTP requests
- authenticate users
- validate request data
- call services
- return HTTP responses

Business logic should not be buried inside controllers.

### Service layer

Services handle business logic.

Examples:

- create an asset request
- create Zendesk ticket
- sync Zendesk state
- produce dashboard data

This keeps controllers small and easier to explain.

---

# 6. Folder Structure

Keep the structure simple.

```text
it-asset-request-tool/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── asset_request.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── controllers/
│   │   │   ├── request_controller.py
│   │   │   ├── dashboard_controller.py
│   │   │   └── zendesk_controller.py
│   │   │
│   │   ├── services/
│   │   │   ├── request_service.py
│   │   │   └── zendesk_service.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging_config.py
│   │   │
│   │   ├── schemas.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_requests.py
│   │   ├── test_auth.py
│   │   └── test_zendesk.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── RequestView.jsx
│   │   │   ├── RequestDetailView.jsx
│   │   │   └── DashboardView.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── AssetRequestForm.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   └── DashboardCard.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── .env.example
│
├── .gitignore
├── README.md
└── PROJECT_SPEC.md
```

Avoid adding more folders unless the code genuinely becomes difficult to manage.

---

# 7. Authentication Decision

## Authentication IS required.

The original interview requirement explicitly asks for:

> Basic Auth — simulate a logged-in user.

Therefore authentication should not be removed.

However, keep it extremely simple.

### Design

Use **one demo user** defined in backend environment variables.

Example:

```env
APP_USERNAME=demo
APP_PASSWORD=change-me
```

FastAPI uses HTTP Basic authentication.

No user database is required.

No registration is required.

No password reset is required.

No JWT is required.

No OAuth is required.

### Frontend

Provide a very small login screen or login modal.

The entered credentials can be held in:

- React state; or
- sessionStorage for the demo session.

Do **not** hardcode the password into the frontend source code.

The frontend sends:

```text
Authorization: Basic <encoded-credentials>
```

with protected API requests.

### Swagger

FastAPI Swagger should also expose the Basic Auth scheme so the interviewer can click:

**Authorize**

and test the API manually.

### Why this design

It satisfies the interview security requirement while keeping the application understandable.

In a real company environment this would normally be replaced by:

- Active Directory
- Microsoft Entra ID
- OAuth/OIDC
- SSO

but those are outside the scope of this exercise.

---

# 8. Application Pages

The frontend should contain three functional views.

---

## Page 1 — Asset Request Form

Route:

```text
/request
```

Fields:

- Requester name
- Requester email
- Asset type
- Business reason / justification

Suggested asset options:

- Laptop
- Monitor
- Mouse
- Keyboard
- Headset
- Docking Station
- Other

Validation:

- requester name required
- valid email required
- asset type must be from allowed list
- reason required
- minimum reasonable reason length
- maximum input lengths

Submit button:

```text
Submit IT Asset Request
```

On successful submission show:

- internal request ID
- current status
- Zendesk ticket ID if available
- link to request detail page

Example:

```text
Request successfully submitted.

Request ID: 27
Status: New
Zendesk Ticket: #12345
```

If Zendesk creation fails:

```text
Request successfully saved.

Request ID: 27
Zendesk synchronisation is pending.
```

The user request must **never be lost merely because Zendesk failed**.

---

# 9. Page 2 — Request Detail / Tracking

Route:

```text
/requests/:id
```

Display:

- Request ID
- Requester
- Asset
- Reason
- Internal status
- Zendesk ticket ID
- Zendesk status
- Created date/time
- Last updated date/time
- Last Zendesk sync
- Sync state

Example:

```text
Request #27

Asset: Laptop
Requested By: Mohammed Farhaan Buckas

Internal Status: Open
Zendesk Ticket: #12345
Zendesk Status: Open

Last Synced:
10 Sep 2026 14:42
```

Button:

```text
Refresh from Zendesk
```

This calls the manual reconciliation endpoint.

---

# 10. Page 3 — IT Asset Dashboard

Route:

```text
/dashboard
```

Purpose:

Provide a simple operational view of how the request platform is being used.

### Summary cards

Show:

- Total Requests
- New Requests
- Open Requests
- Pending Requests
- Solved Requests
- Sync Failures

Example:

```text
Total Requests     42
Open Requests      11
Pending             2
Solved             29
Sync Failures       0
```

### Requests by asset type

Example:

```text
Laptop          18
Mouse           11
Monitor          6
Keyboard         4
Headset          3
```

A simple bar chart is optional.

Do not introduce a chart library unless necessary.

A clean table or CSS bar display is sufficient.

### Recent requests table

Columns:

```text
Request ID
Requester
Asset
Internal Status
Zendesk Ticket
Zendesk Status
Created
```

### Integration health

Display:

```text
Zendesk Integration: Connected
Last Successful Sync: 10 Sep 2026 14:42
Sync Failures: 0
```

### Business purpose

The dashboard demonstrates that the application is not only collecting requests.

It also supports:

- operational visibility
- usage monitoring
- workload analysis
- asset-demand patterns
- helpdesk integration health
- exception identification

---

# 11. Database Design

## Table: asset_requests

Suggested fields:

```text
id
requester_name
requester_email
asset_type
reason

status

zendesk_ticket_id
zendesk_status
zendesk_sync_status
zendesk_last_synced_at

created_at
updated_at
```

### Suggested internal statuses

```text
new
open
pending
solved
sync_pending
sync_failed
```

Do not overcomplicate workflow states.

---

## Table: audit_logs

Suggested fields:

```text
id
request_id
event_type
source
message
created_at
```

Examples of event types:

```text
REQUEST_CREATED
REQUEST_UPDATED

ZENDESK_TICKET_CREATED
ZENDESK_CREATE_FAILED

ZENDESK_WEBHOOK_RECEIVED
ZENDESK_STATUS_CHANGED

MANUAL_SYNC_STARTED
MANUAL_SYNC_COMPLETED
MANUAL_SYNC_FAILED
```

### Why keep an audit table?

The audit table makes it possible to answer:

- what happened
- when it happened
- which system caused the change
- whether a failed integration was later recovered

This demonstrates operational traceability.

---

# 12. Request Creation Flow

```text
User fills form
        ↓
React performs basic validation
        ↓
POST /api/requests
        ↓
Basic Auth
        ↓
Pydantic validation
        ↓
Create database record
        ↓
Write audit record
        ↓
Attempt Zendesk ticket creation
        ↓
     ┌───────────────┐
     │               │
   Success          Failure
     │               │
     ▼               ▼
Store Zendesk ID   Mark sync_pending
     │               │
     └───────┬───────┘
             ↓
       Return response
             ↓
       Show result to user
```

The database save is the primary transaction.

Zendesk is a secondary integration.

---

# 13. Zendesk Sandbox Integration

Use the authorised CX Experts Zendesk sandbox available for consulting / side-project demonstrations.

The Zendesk subdomain, API credentials and tokens must be stored in environment variables.

Never commit Zendesk credentials into GitHub.

Example variables:

```env
ZENDESK_SUBDOMAIN=digify7
ZENDESK_EMAIL=
ZENDESK_API_TOKEN=
ZENDESK_WEBHOOK_SECRET=
```

The screenshot supplied shows the sandbox at:

```text
digify7.zendesk.com
```

Do not place real secrets in this specification or repository.

---

# 14. Creating the Zendesk Ticket

After the local request has been stored successfully, call Zendesk.

Suggested ticket:

```text
Subject:
IT Asset Request | Laptop | Mohammed Farhaan Buckas
```

Body:

```text
IT Asset Request

Internal Request ID: 27
Requester: Mohammed Farhaan Buckas
Email: user@example.com
Asset: Laptop

Business Reason:
Replacement required for current damaged device.
```

Optional Zendesk tags:

```text
it_asset_request
asset_laptop
source_asset_portal
```

Store the returned Zendesk ticket ID in:

```text
asset_requests.zendesk_ticket_id
```

---

# 15. Two-Way Zendesk Synchronisation

The application should support two sync methods.

## Primary Method — Zendesk Webhook

When the Zendesk ticket changes status, Zendesk should send the application an event.

Endpoint:

```text
POST /api/webhooks/zendesk
```

Example payload:

```json
{
  "ticket_id": 12345,
  "request_id": 27,
  "status": "pending"
}
```

Processing:

```text
Zendesk ticket changes
        ↓
Zendesk trigger
        ↓
Webhook POST
        ↓
FastAPI verifies webhook
        ↓
Find request
        ↓
Update Zendesk status
        ↓
Update last sync time
        ↓
Write audit record
        ↓
Dashboard reflects new state
```

### Webhook security

For the interview version, use a shared secret header.

Example:

```text
X-Webhook-Secret
```

The backend compares the header against:

```env
ZENDESK_WEBHOOK_SECRET=
```

Reject invalid requests.

If time allows and Zendesk supports stronger webhook signing in the selected configuration, that can be discussed as a production enhancement.

Do not make it a requirement for the demo.

---

# 16. Manual Zendesk Reconciliation

Webhooks can fail.

Therefore also provide a manual sync endpoint.

```text
POST /api/requests/{id}/sync
```

Flow:

```text
User presses Refresh from Zendesk
        ↓
FastAPI retrieves local request
        ↓
Find Zendesk ticket ID
        ↓
GET Zendesk ticket
        ↓
Compare Zendesk state with local state
        ↓
Update local state
        ↓
Write audit event
        ↓
Return updated request
```

### Why both?

Webhook:

- event driven
- near real time
- fewer API requests

Manual sync:

- recovery mechanism
- useful for troubleshooting
- handles missed webhook events

Interview explanation:

> The webhook is the primary event-driven integration. Manual reconciliation is the fallback so the local application can recover if an event is missed.

---

# 17. API Endpoints

Keep the API small.

## Health

```text
GET /health
```

Returns:

```json
{
  "status": "ok"
}
```

---

## Requests

```text
POST /api/requests
```

Create request.

```text
GET /api/requests
```

List requests.

```text
GET /api/requests/{id}
```

Retrieve one request.

```text
POST /api/requests/{id}/sync
```

Refresh state from Zendesk.

---

## Dashboard

```text
GET /api/dashboard/summary
```

Example response:

```json
{
  "total_requests": 42,
  "new_requests": 4,
  "open_requests": 7,
  "pending_requests": 2,
  "solved_requests": 29,
  "sync_failures": 0,
  "last_successful_sync": "2026-09-10T14:42:00",
  "by_asset_type": {
    "Laptop": 18,
    "Mouse": 11,
    "Monitor": 6,
    "Keyboard": 4,
    "Headset": 3
  }
}
```

---

## Zendesk Webhook

```text
POST /api/webhooks/zendesk
```

Receives selected Zendesk status events.

---

# 18. Swagger / OpenAPI

FastAPI automatically exposes API documentation.

Use:

```text
/docs
```

for Swagger UI.

Swagger should show:

- HTTP Basic authentication
- request schemas
- response schemas
- request validation
- all API endpoints

The interviewer should be able to use Swagger to test the backend without the React interface.

This demonstrates that the frontend is only one possible API consumer.

---

# 19. Validation

Validation should occur at two levels.

## Frontend

React should provide friendly user feedback.

Examples:

- required fields
- valid email
- allowed asset type
- character limits

## Backend

The backend is the authoritative validation layer.

Use Pydantic.

Examples:

```text
requester_name:
minimum 2 characters
maximum 100 characters

email:
valid email address

asset_type:
must be in approved asset list

reason:
minimum 10 characters
maximum 1000 characters
```

Never trust frontend validation alone.

---

# 20. SQL Injection Protection

Do not construct SQL statements by inserting user input into strings.

Bad:

```python
query = f"SELECT * FROM requests WHERE email = '{email}'"
```

Use SQLAlchemy ORM queries / parameterised SQL instead.

This prevents user input from becoming executable SQL.

---

# 21. XSS Protection

XSS means:

**Cross-Site Scripting**

Example malicious input:

```html
<script>
stealData()
</script>
```

The application must never intentionally render user text as executable HTML.

React escapes normal text values by default.

Therefore:

- render values normally
- do not use `dangerouslySetInnerHTML`
- validate and limit input
- do not inject raw HTML returned by users

Interview explanation:

> I rely on React's normal escaped rendering and avoid injecting user-controlled raw HTML into the page.

---

# 22. Logging

Two logging layers are useful.

## Application log

Python logging records technical events.

Examples:

```text
request received
database write successful
Zendesk API request started
Zendesk ticket created
Zendesk API error
webhook received
manual sync completed
```

Do not log:

- passwords
- API tokens
- Basic Auth headers
- secrets

## Audit log

Database audit events represent important business/system events.

This separates normal technical logs from durable audit history.

---

# 23. Error Handling

Expected failures should return meaningful HTTP responses.

Examples:

```text
400 Bad Request
401 Unauthorized
404 Request Not Found
422 Validation Error
500 Internal Server Error
502 Zendesk Integration Error
```

However, Zendesk failure during request creation should generally **not** fail the primary asset request.

Example:

```text
Database write: success
Zendesk create: failure

Result:
201 Created

zendesk_sync_status = "sync_pending"
```

This prevents a third-party outage from destroying the user's request.

---

# 24. CORS

Frontend and backend will be deployed on different domains.

Example:

```text
Frontend:
https://asset-request.vercel.app

Backend:
https://asset-request-api.onrender.com
```

FastAPI should therefore configure CORS.

Allowed origins should come from an environment variable.

Example:

```env
FRONTEND_URL=https://asset-request.vercel.app
```

Do not blindly permit every origin in the final deployed version.

---

# 25. Environment Variables

Backend `.env.example`:

```env
APP_USERNAME=
APP_PASSWORD=

DATABASE_URL=

FRONTEND_URL=

ZENDESK_SUBDOMAIN=digify7
ZENDESK_EMAIL=
ZENDESK_API_TOKEN=
ZENDESK_WEBHOOK_SECRET=
```

Frontend `.env.example`:

```env
VITE_API_URL=
```

Real `.env` files must be ignored by Git.

---

# 26. Database Strategy

## Local

Use SQLite.

Example:

```env
DATABASE_URL=sqlite:///./asset_requests.db
```

Benefits:

- no database server required
- fast setup
- easy local testing

## Hosted

Use **Render PostgreSQL**.

The hosted demo architecture is intentionally standardised on Render:

```text
Frontend        → Vercel
Backend         → Render Web Service
Database        → Render PostgreSQL
Helpdesk        → Zendesk sandbox
Source control  → GitHub
```

The application must use `DATABASE_URL` so the same SQLAlchemy code can run against:

```env
# Local development
DATABASE_URL=sqlite:///./asset_requests.db
```

and:

```env
# Hosted deployment
DATABASE_URL=postgresql://<render-postgres-connection-string>
```

Do not add Supabase, Neon, Firebase or another database platform unless Render PostgreSQL is unavailable.

This keeps the interview environment simple and reduces the number of external services that need to be configured or explained.

---

# 27. Deployment Plan — Build for Render + Vercel from Day One

The application must be structured so the same codebase works locally and in the hosted demo without architectural rewrites.

## Frontend — Vercel

Deploy the React/Vite frontend to Vercel.

Required frontend environment variable:

```env
VITE_API_URL=https://<render-backend-url>
```

Rules:

- never hardcode the backend URL in React components
- all API requests must use `VITE_API_URL`
- frontend routes must work correctly on Vercel refresh/navigation
- the app must display useful loading and API-error states
- no backend credentials or Zendesk secrets may exist in Vercel client-side variables

## Backend — Render

Deploy FastAPI to Render.

Requirements:

- backend must bind to the host/port expected by Render
- deployment start command must be documented in README
- `/health` must remain unauthenticated so Render and the interviewer can verify service health
- all protected business endpoints must use Basic Auth
- CORS must allow the Vercel production URL and localhost development URL
- database and Zendesk credentials must come only from environment variables
- backend must not depend on local filesystem persistence

Suggested production variables:

```env
APP_USERNAME=
APP_PASSWORD=
DATABASE_URL=
FRONTEND_URL=https://<vercel-frontend-url>
ZENDESK_SUBDOMAIN=digify7
ZENDESK_EMAIL=
ZENDESK_API_TOKEN=
ZENDESK_WEBHOOK_SECRET=
```

## Database — Render PostgreSQL

Hosted deployment must use **Render PostgreSQL**.

The application must not rely on SQLite in the Render-hosted production/demo environment.

Local development may use:

```env
DATABASE_URL=sqlite:///./asset_requests.db
```

Hosted deployment uses the Render PostgreSQL connection string:

```env
DATABASE_URL=postgresql://<render-postgres-connection-string>
```

The application code must select the database entirely through `DATABASE_URL`.

### Render PostgreSQL Rules

- create the database in Render before deploying the backend
- use the Render-provided PostgreSQL connection string
- store the connection string only as a Render environment variable
- never commit the database URL or password
- do not hardcode PostgreSQL credentials in source code
- verify the FastAPI backend can create/read records before deploying the frontend
- use the same SQLAlchemy models locally and when hosted

## Zendesk Webhook

Zendesk sandbox trigger sends updates to:

```text
https://<render-backend-url>/api/webhooks/zendesk
```

The webhook endpoint must:

- be publicly reachable
- not use frontend Basic Auth
- validate `X-Webhook-Secret`
- reject an incorrect/missing secret
- write an audit event for accepted updates
- update the matching local request safely

## Deployment Order

Use this order:

```text
1. Create Render PostgreSQL
2. copy the Render PostgreSQL connection string into the backend `DATABASE_URL`
3. deploy the FastAPI backend to Render
4. verify `/health` and `/docs`
5. test database create/read operations on the hosted backend
6. configure the Vercel frontend with `VITE_API_URL`
7. deploy the Vercel frontend
8. add the Vercel URL to backend `FRONTEND_URL` / CORS
9. configure the Zendesk webhook to the Render backend URL
10. run the complete end-to-end test
```

The deployed system should be demonstrable entirely from the browser.

---

# 28. Testing

Keep tests focused.

Required tests:

1. health endpoint returns success
2. protected endpoint rejects bad credentials
3. valid asset request returns success
4. invalid email is rejected
5. invalid asset type is rejected
6. missing reason is rejected
7. request persists to database
8. Zendesk success stores ticket ID
9. Zendesk failure preserves the local request
10. Zendesk webhook updates ticket status
11. invalid webhook secret is rejected
12. manual sync updates the local state

Do not chase a meaningless test count.

Tests should cover the behaviour most likely to break the business workflow.

---

# 29. Git / GitHub Workflow — Pull Requests Throughout the Build

The repository must demonstrate controlled Git workflow while Codex is building it.

Do **not** build the entire application in one branch and make one final push.

Do **not** push directly to `main` except for the initial repository setup if absolutely required.

`main` should remain the stable branch.

Use small feature branches and pull requests.

## Required branch / PR sequence

### PR 1 — Project Scaffold

Branch:

```text
chore/project-scaffold
```

Contains:

- frontend scaffold
- backend scaffold
- folder structure
- `.gitignore`
- `.env.example`
- README skeleton
- health endpoint

Commit examples:

```text
chore: scaffold React and FastAPI applications
chore: add environment templates and repository structure
```

Open PR → review diff → confirm app starts → merge.

---

### PR 2 — Core Request API + Persistence

Branch:

```text
feat/core-request-api
```

Contains:

- database connection
- models
- schemas
- repository
- request service
- request endpoints
- audit records
- initial tests

Commit examples:

```text
feat: add asset request model and persistence
feat: add request API and audit logging
test: add request API tests
```

Open PR → run tests → review → merge.

---

### PR 3 — Authentication + Security

Branch:

```text
feat/auth-security
```

Contains:

- Basic Auth
- environment-based credentials
- backend validation
- security-related error handling
- CORS
- security tests

Commit examples:

```text
feat: add Basic Auth protection
feat: configure validation and CORS
test: add authentication and validation tests
```

Open PR → test → review → merge.

---

### PR 4 — React Request UI

Branch:

```text
feat/request-ui
```

Contains:

- request form
- frontend validation
- API client
- success/error states
- request detail view

Commit examples:

```text
feat: add authenticated asset request form
feat: add request detail and error states
```

Open PR → test locally → review → merge.

---

### PR 5 — Zendesk Integration

Branch:

```text
feat/zendesk-integration
```

Contains:

- Zendesk ticket creation
- returned ticket ID storage
- failure isolation
- Zendesk service
- Zendesk tests

Commit examples:

```text
feat: add Zendesk sandbox ticket creation
feat: preserve request when Zendesk sync fails
test: add Zendesk service tests
```

Open PR → verify with sandbox → review → merge.

---

### PR 6 — Zendesk Webhook + Reconciliation

Branch:

```text
feat/zendesk-sync
```

Contains:

- webhook endpoint
- webhook secret validation
- local status update
- audit events
- manual reconciliation endpoint
- sync tests

Commit examples:

```text
feat: add Zendesk status webhook
feat: add manual Zendesk reconciliation
test: add webhook and sync tests
```

Open PR → test webhook → review → merge.

---

### PR 7 — Dashboard

Branch:

```text
feat/operations-dashboard
```

Contains:

- summary API
- KPI cards
- asset breakdown
- recent requests
- Zendesk status/sync health

Commit examples:

```text
feat: add dashboard summary API
feat: add IT operations dashboard
```

Open PR → review → merge.

---

### PR 8 — Render + Vercel Deployment

Branch:

```text
chore/deployment
```

Contains:

- production environment handling
- deployment configuration
- Vercel settings/config if required
- Render start command/config
- PostgreSQL compatibility fixes
- README deployment instructions

Commit examples:

```text
chore: prepare FastAPI backend for Render
chore: prepare React frontend for Vercel
docs: add hosted deployment guide
```

Open PR → verify preview/deployment → merge.

---

### PR 9 — Final Tests + Documentation

Branch:

```text
chore/final-hardening
```

Contains:

- final test fixes
- README completion
- architecture diagram
- known limitations
- demo instructions
- cleanup

Commit examples:

```text
test: complete integration test coverage
docs: complete architecture and demo guide
chore: final project cleanup
```

Open PR → final review → merge.

---

## Pull Request Rules for Codex

For every feature phase, Codex must:

1. pull the latest `main`
2. create the named feature branch
3. make only the changes for that phase
4. use small logical commits
5. run relevant tests before pushing
6. push the feature branch
7. open a pull request
8. provide a short PR summary:
   - what changed
   - why
   - how tested
   - known limitations
9. wait for review/approval before merging if operating interactively
10. merge only after tests pass
11. delete the feature branch after merge where practical
12. start the next phase from the newly updated `main`

The interview value is not merely that GitHub contains the code.

The repository should visibly show:

```text
feature branch
      ↓
logical commits
      ↓
pull request
      ↓
review / tests
      ↓
merge
      ↓
deployment
```

This demonstrates the Git governance principles discussed in the role.

---

# 30. User Journey

```text
User signs in
      ↓
Opens asset request form
      ↓
Completes request
      ↓
Request validated
      ↓
Request saved to SQL
      ↓
Zendesk ticket created
      ↓
User receives request ID
      ↓
IT works ticket in Zendesk
      ↓
Zendesk status changes
      ↓
Webhook updates application
      ↓
User checks request status
      ↓
Dashboard shows operational state
```

---

# 31. Demo Scenario

Prepare predictable demo data.

### Demo 1

Create:

```text
Requester:
Mohammed Farhaan Buckas

Asset:
Laptop

Reason:
Replacement laptop required for development and client implementation work.
```

Show:

1. frontend validation
2. successful submission
3. local request ID
4. Zendesk ticket ID
5. database persistence
6. Zendesk ticket
7. Swagger endpoint
8. dashboard update

### Demo 2

Change the Zendesk ticket from:

```text
New
```

to:

```text
Pending
```

Show:

1. Zendesk trigger fires webhook
2. backend receives webhook
3. database status updates
4. dashboard reflects change

### Demo 3

Use:

```text
Refresh from Zendesk
```

to demonstrate manual reconciliation.

---

# 32. 10–15 Minute Interview Presentation Order

Do not walk through every source file.

Present the system.

## Minute 0–2 — Requirement

Explain:

> The requirement was to build a simple authenticated IT asset request application with persistence, validation, logging and GitHub-hosted code.

Then add:

> I extended the helpdesk simulation into a real Zendesk sandbox integration because that is an area I already work with professionally.

---

## Minute 2–4 — Architecture

Show:

```text
React
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Zendesk
  ↕
Webhook
```

Explain MVC mapping.

---

## Minute 4–7 — Live Demo

Create an asset request.

Show:

- validation
- successful save
- ticket creation
- request tracking

---

## Minute 7–9 — Dashboard

Show:

- request totals
- statuses
- asset demand
- sync health
- recent requests

---

## Minute 9–11 — API / Swagger

Show `/docs`.

Demonstrate:

- authentication
- schemas
- POST request
- status endpoint

---

## Minute 11–13 — Security / Reliability

Explain:

- backend validation
- SQLAlchemy parameterisation
- React XSS protection
- Basic Auth
- environment variables
- webhook secret
- audit logging
- Zendesk failure recovery

---

## Minute 13–15 — Trade-offs

Explain intentionally simple choices.

Examples:

> I used Basic Auth because it was explicitly requested. In production I would normally integrate company SSO.

> I used a monolithic FastAPI backend because the scope does not justify microservices.

> Zendesk is a secondary integration so an outage does not cause asset requests to disappear.

> The webhook is the primary sync method, while manual reconciliation provides a recovery path.

These are valuable engineering decisions.

---

# 33. Questions the Interviewer May Ask

Be ready to explain:

### Why FastAPI?

Simple Python API framework with validation, routing and automatic OpenAPI/Swagger support.

### Why React?

Matches the team's frontend technology direction and gives a clean component-based interface.

### Why PostgreSQL?

Reliable relational persistence for hosted deployment.

### Why SQLite locally?

Removes infrastructure setup from local development.

### Why store the Zendesk ID?

It creates a durable relationship between the application request and the helpdesk workflow.

### Why a webhook?

Zendesk can notify the application when state changes instead of the application repeatedly polling Zendesk.

### Why manual sync as well?

Recovery if a webhook is missed or the systems temporarily become inconsistent.

### Why an audit table?

Operational traceability.

### What happens if Zendesk goes down?

The local request is still saved and marked for retry/sync.

### Why Basic Auth?

It directly satisfies the exercise requirement while remaining simple enough for the prototype.

### What would you change in production?

Possible improvements:

- company SSO / Entra ID
- role-based access control
- stronger webhook signing
- automated retry worker
- alerting
- structured centralised logging
- database migrations
- CI/CD
- infrastructure monitoring
- approval workflow
- asset inventory integration

---

# 34. Codex Implementation Rules

Codex should treat this file as the project specification.

## Important instructions

1. Keep the architecture simple.
2. Do not add unnecessary frameworks.
3. Do not add microservices.
4. Do not remove Basic Auth.
5. Do not hardcode secrets.
6. Do not commit `.env`.
7. Do not expose Zendesk credentials to the frontend.
8. The database write is the primary transaction.
9. Zendesk failure must not cause request loss.
10. Use SQLAlchemy for persistence.
11. Use Pydantic for API schemas and validation.
12. Use React/Vite for the frontend.
13. Use FastAPI for the backend.
14. Keep controllers thin.
15. Put business logic in services.
16. Use React's normal safe text rendering.
17. Do not use `dangerouslySetInnerHTML`.
18. Add `/health`.
19. Add Swagger/OpenAPI.
20. Add automated tests.
21. Make the UI clean and professional but not excessive.
22. Every major file should be understandable by a developer reviewing the project for the first time.
23. Prefer readable code over clever abstractions.
24. Add comments only where the purpose is not obvious from the code.
25. Document every environment variable in README.
26. Ensure local startup is straightforward.
27. Ensure the deployed frontend can call the deployed backend through configured CORS.
28. Do not invent features outside this specification unless required to make the application function.

---

# 35. Codex Build Order

Codex should build in this order.

### Phase 1 — Scaffold

Create:

- backend
- frontend
- folder structure
- requirements
- environment examples
- README skeleton
- `/health`

Complete this work in:

```text
chore/project-scaffold
```

Open the first pull request.

Once the architecture matches this specification and the scaffold starts successfully, continue through the remaining phases using the PR workflow defined in Section 29.

### Phase 2 — Core Backend

Build:

- database connection
- models
- schemas
- Basic Auth
- request API
- logging
- tests

### Phase 3 — Frontend

Build:

- login interaction
- request form
- request detail page
- API client
- validation

### Phase 4 — Zendesk

Build:

- ticket creation
- Zendesk ticket ID storage
- webhook
- manual sync
- failure handling
- tests

### Phase 5 — Dashboard

Build:

- dashboard summary endpoint
- summary cards
- request table
- asset breakdown
- Zendesk sync health

### Phase 6 — Deployment

Prepare:

- Vercel frontend
- Render backend
- Render PostgreSQL connection
- CORS
- environment variables

### Phase 7 — Documentation

Complete:

- README
- architecture explanation
- setup guide
- endpoint list
- security decisions
- deployment instructions
- known limitations

---

# 36. Definition of Done

The project is complete when:

- [ ] frontend loads
- [ ] authentication works
- [ ] asset form validates input
- [ ] asset request saves to SQL
- [ ] audit event is created
- [ ] Zendesk ticket is created
- [ ] Zendesk ticket ID is stored
- [ ] Zendesk failure does not lose the request
- [ ] webhook can update Zendesk status locally
- [ ] manual Zendesk sync works
- [ ] request detail page displays current state
- [ ] dashboard loads summary information
- [ ] Swagger works
- [ ] secrets are in environment variables
- [ ] SQL injection is mitigated
- [ ] raw user HTML is not rendered
- [ ] tests pass
- [ ] repository is on GitHub
- [ ] deployed frontend works
- [ ] deployed backend works
- [ ] hosted database persists data
- [ ] README explains setup and architecture
- [ ] candidate can explain every major file and workflow

---

# 37. Locked Hosting Architecture

The hosting choice is final for this interview project unless a platform failure forces a change.

```text
┌──────────────────────────┐
│ React + Vite             │
│ Vercel                   │
└────────────┬─────────────┘
             │ HTTPS / JSON
             ▼
┌──────────────────────────┐
│ FastAPI                  │
│ Render Web Service       │
└───────┬───────────┬──────┘
        │           │
        ▼           ▼
┌──────────────┐  ┌──────────────┐
│ Render       │  │ Zendesk      │
│ PostgreSQL   │  │ Sandbox      │
└──────────────┘  └──────────────┘
```

### Local development

```text
React/Vite localhost
        ↓
FastAPI localhost
        ↓
SQLite
```

### Hosted interview demo

```text
Vercel
   ↓
Render FastAPI
   ↓
Render PostgreSQL
   ↕
Zendesk Sandbox
```

### Why this setup

- **SQLite locally** keeps development and testing easy.
- **Render PostgreSQL hosted** gives the deployed demo durable SQL persistence.
- **Render** keeps backend and hosted database administration in one place.
- **Vercel** provides straightforward React/Vite hosting.
- **Zendesk Sandbox** demonstrates a real external business-system integration.
- **GitHub PRs** demonstrate source-control governance throughout development.

Do not introduce a second hosted database provider merely for experimentation.

---

# 37. Final Principle

The application should demonstrate this engineering approach:

```text
Operational problem
        ↓
Clear requirements
        ↓
Simple architecture
        ↓
Validated request
        ↓
Durable persistence
        ↓
Controlled integration
        ↓
Auditability
        ↓
Operational visibility
        ↓
Recoverable failure
```

The objective is not to build the largest system.

The objective is to build a **small system that works, can be explained clearly, and shows sound technical judgement**.


---

# 38. Codex Execution Instruction

After reading this specification, Codex may proceed with the full build.

Codex should **not** stop after merely describing the architecture unless a blocking ambiguity exists.

Use the specification as the source of truth and build the application phase by phase.

For each phase:

```text
latest main
    ↓
new feature branch
    ↓
implementation
    ↓
tests
    ↓
logical commits
    ↓
push
    ↓
pull request
    ↓
review / merge
    ↓
next phase from updated main
```

The final solution must be designed specifically for:

```text
React / Vite frontend → Vercel
FastAPI backend       → Render
SQL persistence       → Render PostgreSQL
Helpdesk integration  → Zendesk sandbox
Source control        → GitHub + pull requests
```

Do not postpone deployment concerns until the end if an earlier architectural choice would prevent the application from working on Render or Vercel.

Prefer the simplest implementation that satisfies the requirement and remains easy to explain in an interview.

Codex should proceed until the Definition of Done is satisfied.
