# IT Asset Request Tool — Technical Interview Project Specification

**Candidate:** Mohammed Farhaan Buckas  
**Purpose:** Royal Tyres technical interview practical  
**Project type:** Small full-stack internal IT asset request application  
**Target demo:** Hosted and working end to end  
**Hosting:** React/Vite on Vercel, FastAPI on Render, Render PostgreSQL, Zendesk sandbox  
**Primary design goal:** Keep the system simple enough to explain file by file while demonstrating durable persistence, security, integration safety and controlled configuration.

---

# 1. Project Summary

Build an authenticated internal **IT Asset Request Tool** where an employee can request equipment such as a laptop, monitor, mouse, keyboard, headset, docking station or other approved item.

The application must:

1. provide a React form with validation;
2. submit to a FastAPI backend;
3. persist requests in SQL;
4. protect business endpoints with Basic Auth;
5. prevent SQL injection and unsafe HTML rendering;
6. keep technical logs and a durable audit table;
7. integrate with a real Zendesk sandbox;
8. safely configure the required Zendesk objects through a governed setup screen;
9. keep Zendesk credentials server-side in environment variables;
10. create Zendesk tickets only after the local request is durably committed;
11. store the Zendesk ticket ID and sync state;
12. later support Zendesk webhook status updates and manual reconciliation;
13. provide an operations dashboard;
14. expose Swagger/OpenAPI;
15. use GitHub branches, pull requests and CI.

This remains a **small monolithic application**. Do not introduce microservices, queues, Kubernetes, Terraform, Redis or other infrastructure that the interview requirement does not justify.

---

# 2. Locked Hosted Architecture

```text
┌──────────────────────────────┐
│ React + Vite                 │
│ Vercel                       │
│ royal-tires.vercel.app       │
│                              │
│ Login                        │
│ Asset Request                │
│ Request Tracking             │
│ Zendesk Setup                │
│ Dashboard                    │
└───────────────┬──────────────┘
                │ HTTPS / JSON / Basic Auth
                ▼
┌──────────────────────────────┐
│ FastAPI                      │
│ Render                       │
│ royal-tires-api.onrender.com │
│                              │
│ Controllers                  │
│ Validation                   │
│ Services                     │
│ Security                     │
│ Audit logging                │
│ Zendesk env credentials      │
└─────────┬───────────┬────────┘
          │           │
          ▼           ▼
┌─────────────────┐  ┌────────────────────┐
│ Render Postgres │  │ Zendesk Sandbox    │
│                 │  │                    │
│ asset_requests  │  │ Brand              │
│ audit_logs      │  │ Group              │
│ zendesk_connection│ │ Fields             │
└─────────────────┘  │ Form               │
                     │ View               │
                     │ Tickets            │
                     └────────────────────┘
```

Local development may use SQLite through the same SQLAlchemy models.

---

# 3. MVC Mapping

**Model**

- `AssetRequest`
- `AuditLog`
- `ZendeskConnection`
- SQLAlchemy
- SQLite locally / PostgreSQL hosted

**View**

- React/Vite
- Login
- Request form
- Request tracking
- Zendesk setup
- Dashboard

**Controller**

- FastAPI route modules
- authenticate
- validate
- call services
- return HTTP responses

**Service layer**

- request creation
- Zendesk environment credential testing
- Zendesk discovery
- setup planning
- configuration apply/verification
- Zendesk ticket creation
- later webhook/manual sync
- dashboard calculations

Controllers should remain thin.

---

# 4. Interview Requirement Mapping

| Interview requirement | Implementation |
|---|---|
| Frontend form | React + Vite |
| Validation | React + Pydantic |
| Backend API | FastAPI |
| SQL persistence | SQLAlchemy + PostgreSQL hosted / SQLite local |
| SQL injection protection | ORM / parameterised queries |
| XSS protection | React escaped text; never `dangerouslySetInnerHTML` |
| Basic Auth | FastAPI HTTP Basic |
| Logging | Python logging + `audit_logs` |
| GitHub | Feature branches, PRs, CI |
| Helpdesk simulation | Real Zendesk sandbox |
| API documentation | Swagger/OpenAPI |
| Reliability | Local request committed before Zendesk |
| Integration governance | Env credentials → test → discover → dry run → approve → apply → verify |

---

# 5. Application Pages

## `/request`

Fields:

- Requester name
- Requester email
- Asset type
- Business reason

Allowed assets:

- Laptop
- Monitor
- Mouse
- Keyboard
- Headset
- Docking Station
- Other

Successful submission shows local request ID, internal status, Zendesk ticket ID when available and Zendesk sync state.

A Zendesk outage must never lose the local request.

## `/requests/:id`

Display local request details, Zendesk ticket ID/status, sync status and timestamps.

A later phase adds **Refresh from Zendesk**.

## `/zendesk-setup`

Authenticated administration page. It does **not** accept Zendesk credentials from the browser.

It only:

1. shows whether required server-side Zendesk environment variables are present;
2. tests the environment-held credentials;
3. discovers existing Zendesk configuration;
4. shows CREATE/REUSE actions;
5. requires explicit approval;
6. applies the approved configuration;
7. verifies the result.

## `/dashboard`

Later operations view containing totals, status breakdowns, recent requests and Zendesk sync health.

---

# 6. Authentication

The exercise explicitly asks for Basic Auth to simulate a logged-in user.

Backend environment variables:

```env
APP_USERNAME=
APP_PASSWORD=
```

The React login holds credentials only for the browser session and sends:

```text
Authorization: Basic <encoded-credentials>
```

No user database, JWT, password reset, registration or OAuth provider is required.

---

# 7. Security Rules

## SQL injection

Use SQLAlchemy ORM / parameterised queries. Never interpolate user input into SQL strings.

## XSS

React renders user-controlled values as normal text.

**Never use:**

```text
dangerouslySetInnerHTML
```

## Secrets

Never commit or expose:

- Basic Auth password
- database password
- Zendesk API token
- webhook secret

Never log Authorization headers or Zendesk API tokens.

Zendesk credentials remain on the FastAPI/Render side only.

---

# 8. Database Design

## `asset_requests`

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

## `audit_logs`

```text
id
request_id
event_type
source
message
created_at
```

Important events include:

```text
REQUEST_CREATED
ZENDESK_TICKET_CREATED
ZENDESK_CREATE_FAILED
ZENDESK_WEBHOOK_RECEIVED
ZENDESK_STATUS_CHANGED
MANUAL_SYNC_STARTED
MANUAL_SYNC_COMPLETED
MANUAL_SYNC_FAILED
```

## `zendesk_connection`

This table stores verified Zendesk metadata and managed object IDs only.

```text
id
subdomain
api_email
connected_user_name
connected_user_email
connected_user_role
brand_id
group_id
ticket_form_id
asset_type_field_id
local_request_id_field_id
request_source_field_id
view_id
connected_at
configured_at
verified_at
```

**The Zendesk API token is not stored in PostgreSQL.** It stays in the Render environment.

---

# 9. Zendesk Credential Architecture — ENV METHOD

Zendesk credentials are configured in the backend environment:

```env
ZENDESK_SUBDOMAIN=digify7
ZENDESK_EMAIL=<zendesk-admin-email>
ZENDESK_API_TOKEN=<secret-token>
```

The frontend never receives these values.

Flow:

```text
Render environment
        ↓
FastAPI settings
        ↓
POST /api/zendesk/connect
        ↓
GET Zendesk /api/v2/users/me.json
        ↓
Credentials valid
        ↓
Store only safe connection metadata in PostgreSQL
        ↓
Discover existing Zendesk configuration
        ↓
Return dry-run plan to browser
```

Changing Zendesk environment credentials requires re-testing the connection before configuration can be applied or tickets created.

---

# 10. Zendesk Safe Setup Workflow

This follows the same controlled deployment pattern used in the AI Site Factory / Zendesk configuration tooling: read first, stage a plan, require human approval, then perform the external action.

```text
ENV CREDENTIALS
   ↓
TEST CONNECTION
   ↓
READ EXISTING CONFIGURATION
   ↓
BUILD DRY-RUN PLAN
   ↓
DISPLAY CREATE / REUSE ACTIONS
   ↓
GENERATE PLAN FINGERPRINT
   ↓
EXPLICIT USER APPROVAL
   ↓
RE-READ ZENDESK
   ↓
COMPARE CURRENT PLAN TO APPROVED FINGERPRINT
   ├─ changed → STOP / 409 / review again
   └─ same    → APPLY
                  ↓
               READ BACK
                  ↓
               VERIFY AFTER
```

**Connection testing and dry-run discovery are read-only.**

No Brand, Group, Field, Form or View is created until the authenticated user clicks **Apply configuration** after reviewing the exact plan.

---

# 11. Zendesk Discovery

After the environment credentials are validated, the backend reads current Zendesk configuration through the API.

Required discovery endpoints:

```text
GET /api/v2/users/me.json
GET /api/v2/brands.json
GET /api/v2/groups.json
GET /api/v2/ticket_fields.json
GET /api/v2/ticket_forms.json
GET /api/v2/views.json
```

Discovery follows pagination where present.

Objects are matched by exact Royal Tyres names so repeated setup is idempotent.

Unrelated Zendesk configuration must never be deleted.

---

# 12. Required Zendesk Configuration

## Brand

```text
Royal Tyres
```

Reuse an exact existing Brand or create it.

## Group

```text
Royal Tyres | IT Service Desk
```

Reuse an exact existing Group or create it.

## Custom ticket fields

### Asset Type

```text
RT | Asset Type
```

Dropdown values:

```text
Laptop          -> laptop
Monitor         -> monitor
Mouse           -> mouse
Keyboard        -> keyboard
Headset         -> headset
Docking Station -> docking_station
Other           -> other
```

### Local Request ID

```text
RT | Local Request ID
```

Type: text

### Request Source

```text
RT | Request Source
```

Dropdown value:

```text
Royal Tyres Asset Portal -> royal_tires_asset_portal
```

## Ticket form

```text
Royal Tyres | IT Asset Request
```

Agent-side demo form containing the three Royal Tyres fields and restricted to the Royal Tyres Brand where supported.

## View

```text
Royal Tyres | IT Asset Requests
```

The View filters tickets assigned to the Royal Tyres IT Service Desk Group and carrying `royal_tires_asset_portal`.

The app does not assign a View directly to tickets. Zendesk Views are filters.

---

# 13. Dry-Run Plan and Approval Fingerprint

After connection, show a plan such as:

```text
Brand         CREATE  Royal Tyres
Group         CREATE  Royal Tyres | IT Service Desk
Ticket field  CREATE  RT | Asset Type
Ticket field  CREATE  RT | Local Request ID
Ticket field  CREATE  RT | Request Source
Ticket form   CREATE  Royal Tyres | IT Asset Request
View          CREATE  Royal Tyres | IT Asset Requests
```

Existing exact objects display:

```text
REUSE #<zendesk-id>
```

The backend calculates a SHA-256 fingerprint from the exact plan shown to the administrator.

No mutation occurs while the plan is displayed.

---

# 14. Explicit Apply Confirmation

The administrator must explicitly approve the exact displayed plan.

Frontend wording:

```text
I reviewed this exact dry-run plan. Create only the missing Royal Tyres configuration and do not delete unrelated Zendesk data.
```

API:

```text
POST /api/zendesk/apply
```

Body:

```json
{
  "confirm": true,
  "plan_fingerprint": "<sha256>"
}
```

Immediately before mutation, FastAPI re-reads Zendesk and rebuilds the plan. If its fingerprint differs from the reviewed plan, return HTTP 409 and require a new review.

The configured Zendesk API user must be an admin.

---

# 15. Idempotent Apply Rules

For every managed object:

```text
fresh API read
    ↓
exact Royal Tyres object exists?
    ├─ yes → REUSE existing ID
    └─ no  → CREATE object
```

Apply order:

```text
Brand
  ↓
Group
  ↓
Asset Type field
  ↓
Local Request ID field
  ↓
Request Source field
  ↓
Ticket Form
  ↓
View
```

The apply operation must create only missing Royal Tyres objects, reuse exact existing objects, avoid duplicates, tolerate a partial prior run and never delete unrelated configuration.

---

# 16. Verify After

After apply, read every resulting object back from Zendesk by ID.

Verify:

```text
Brand                PASS / FAIL
Group                PASS / FAIL
Asset Type field     PASS / FAIL
Local Request field  PASS / FAIL
Request Source field PASS / FAIL
Ticket form          PASS / FAIL
View                 PASS / FAIL
```

Only after all managed objects verify successfully should the integration be considered configured.

Persist the verified Zendesk IDs in `zendesk_connection`.

---

# 17. Zendesk Setup API

All endpoints require portal Basic Auth.

## Status / plan

```text
GET /api/zendesk/setup
```

Returns environment presence, connection state, connected instance/user summary, dry-run plan, plan fingerprint, stored object IDs and verification results. It never returns the Zendesk token.

## Test environment connection

```text
POST /api/zendesk/connect
```

No request body is required.

Actions:

1. read `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` from backend settings;
2. validate `/users/me`;
3. store safe connection metadata only;
4. discover current configuration;
5. return the dry-run plan and fingerprint.

No Zendesk configuration is changed.

## Apply

```text
POST /api/zendesk/apply
```

Requires explicit confirmation and the reviewed plan fingerprint. It creates/reuses managed configuration, reads it back and returns verification.

---

# 18. Request Creation Flow

The local database remains the primary system of record.

```text
User submits request
        ↓
React validation
        ↓
POST /api/requests
        ↓
Basic Auth
        ↓
Pydantic validation
        ↓
INSERT asset request
        ↓
INSERT REQUEST_CREATED audit event
        ↓
COMMIT DATABASE
        ↓
Is verified Zendesk setup available?
        ├─ no  → return request with sync_pending
        └─ yes → create Zendesk ticket
                       ↓
                  success / failure
                       ↓
             update local sync fields
                       ↓
                  commit again
```

Zendesk failure must never roll back the already committed request.

---

# 19. Zendesk Ticket Creation

Ticket creation uses backend environment credentials plus verified IDs saved in SQL.

Payload includes:

```text
subject
internal comment
requester
external_id
brand_id
group_id
ticket_form_id
custom_fields
tags
priority
```

Example:

```text
Subject: IT Asset Request #27 - Laptop - Mohammed Farhaan Buckas
External ID: royal-tires-asset-27
Tags: it_asset_request, royal_tires_asset_portal, local_request_27
RT | Asset Type = laptop
RT | Local Request ID = 27
RT | Request Source = royal_tires_asset_portal
```

Store returned Zendesk values:

```text
zendesk_ticket_id
zendesk_status
zendesk_sync_status = synced
zendesk_last_synced_at
```

On Zendesk failure, preserve the local request and set `zendesk_sync_status = sync_failed`.

---

# 20. Later Zendesk Sync

Future PR6:

```text
POST /api/webhooks/zendesk
POST /api/requests/{id}/sync
```

Webhook is the primary event-driven path. Manual reconciliation is the recovery path.

Use `ZENDESK_WEBHOOK_SECRET` for the interview webhook version.

---

# 21. Core API Endpoints

```text
GET  /health
POST /api/requests
GET  /api/requests
GET  /api/requests/{id}

GET  /api/zendesk/setup
POST /api/zendesk/connect
POST /api/zendesk/apply

POST /api/requests/{id}/sync        # later
POST /api/webhooks/zendesk          # later
GET  /api/dashboard/summary         # later
```

Swagger remains available at `/docs`.

---

# 22. Logging

Technical logs may include HTTP method, route, status code, request ID, event type and Zendesk operation result.

Do not log passwords, Authorization headers, Zendesk API tokens or webhook secrets.

The audit table remains separate from operational logs.

---

# 23. CORS

Production frontend:

```text
https://royal-tires.vercel.app
```

Backend:

```text
https://royal-tires-api.onrender.com
```

`FRONTEND_URL` must explicitly allow production and local development origins. Do not use wildcard CORS in the final demo.

---

# 24. Environment Variables

Backend:

```env
APP_USERNAME=
APP_PASSWORD=
DATABASE_URL=
FRONTEND_URL=
ZENDESK_SUBDOMAIN=
ZENDESK_EMAIL=
ZENDESK_API_TOKEN=
ZENDESK_WEBHOOK_SECRET=
```

`ZENDESK_WEBHOOK_SECRET` is only needed when PR6 is implemented.

Frontend:

```env
VITE_API_URL=https://royal-tires-api.onrender.com
```

No server secret may be stored in a Vite environment variable.

---

# 25. Deployment State and Next Order

Base hosting is already established:

```text
Render PostgreSQL       ✓
Render FastAPI          ✓
Vercel React frontend   ✓
Hosted request create   ✓
Hosted request tracking ✓
```

PR5 deployment order:

1. configure `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` on the Render backend;
2. confirm PR5 CI passes;
3. merge PR5;
4. allow Render and Vercel auto-deploy;
5. sign into the Royal Tyres portal;
6. open **Zendesk Setup**;
7. click **Test environment connection**;
8. inspect CREATE/REUSE dry-run plan;
9. tick explicit approval;
10. click **Apply configuration**;
11. verify Brand, Group, Fields, Form and View all return PASS;
12. create a new asset request;
13. confirm the real Zendesk ticket uses the correct Brand, Group, Form and custom fields.

---

# 26. Git / Pull Request Sequence

```text
PR1  chore/project-scaffold       ✓
PR2  feat/core-request-api        ✓
PR3  feat/auth-security           ✓
PR4  feat/request-ui              ✓
PR5  feat/zendesk-integration     CURRENT / DRAFT
PR6  feat/zendesk-sync            later
PR7  feat/operations-dashboard    later
PR8  chore/deployment             mostly completed manually
PR9  chore/final-hardening        later
```

PR5 scope:

- server-side Zendesk env credentials;
- env connection test;
- `/users/me` validation;
- configuration discovery;
- dry-run CREATE/REUSE plan;
- reviewed-plan SHA-256 fingerprint;
- explicit confirmation;
- stale-plan rejection;
- idempotent Brand, Group, Field, Form and View create/reuse;
- post-apply verification;
- persisted safe metadata/object IDs;
- ticket creation using those IDs;
- Zendesk failure isolation;
- tests;
- authenticated React Zendesk setup view.

Do not merge PR5 until CI passes.

---

# 27. CI

GitHub Actions run on pull requests and main.

Backend:

```text
install Python dependencies
pytest
```

Frontend:

```text
npm install
unit tests
vite production build
Playwright Chromium
browser tests
```

Do not merge failing CI.

---

# 28. Testing Requirements

Minimum important behaviours:

1. `/health` returns 200;
2. protected endpoints reject invalid Basic Auth;
3. valid asset request persists;
4. validation rejects invalid input;
5. SQL injection-like input remains harmless data;
6. React renders malicious-looking HTML as text;
7. Zendesk setup reports missing env credentials safely;
8. Zendesk Connect reads credentials from backend environment only;
9. `/users/me` is validated before connection metadata is accepted;
10. Zendesk Connect does not mutate configuration;
11. Apply rejects missing/false confirmation;
12. Apply rejects a stale plan fingerprint;
13. Apply stores managed object IDs;
14. post-apply verification succeeds for created/reused objects;
15. ticket creation uses verified configuration IDs;
16. Zendesk ticket creation success stores ticket ID;
17. Zendesk failure preserves the local request;
18. frontend production build passes;
19. desktop/mobile browser tests pass.

---

# 29. Demo Scenario

## Demo A — Base request

```text
React validation
→ FastAPI
→ PostgreSQL
→ request ID
→ request tracking
```

## Demo B — Governed Zendesk configuration

```text
Render env credentials
→ Zendesk Setup
→ Test environment connection
→ connected admin identity
→ current config discovery
→ CREATE / REUSE dry-run plan
→ plan fingerprint
→ human approval
→ Apply configuration
→ VERIFY AFTER PASS results
```

Then create a request and show the Zendesk ticket with:

```text
Brand: Royal Tyres
Group: Royal Tyres | IT Service Desk
Form: Royal Tyres | IT Asset Request
RT | Asset Type
RT | Local Request ID
RT | Request Source
```

## Demo C — Later two-way sync

Change Zendesk ticket status and demonstrate webhook/manual reconciliation once PR6 exists.

---

# 30. Interview Explanation

> PostgreSQL is the primary system of record, so the employee request is committed before any Zendesk call. Zendesk credentials are held only in the Render backend environment. The setup screen tests those server-side credentials, discovers the live Zendesk configuration and creates a read-only CREATE/REUSE plan. The plan is fingerprinted and must be explicitly approved. Immediately before applying, the backend re-reads Zendesk and rejects the operation if the plan changed. It then creates only missing Royal Tyres objects, verifies them after creation and stores the resulting IDs for ticket creation.

Trade-offs:

- Basic Auth is intentionally simple because it was explicitly requested.
- The app is monolithic because the scope does not justify microservices.
- Zendesk API-token auth is appropriate for the sandbox demo; OAuth would be preferable in a production multi-tenant product.
- Automatic retries/background jobs are deferred.
- The local database remains authoritative when Zendesk is unavailable.

---

# 31. Production Improvements

If this moved beyond the interview demo:

- Entra ID / OIDC / SSO;
- role-based admin permissions;
- Alembic database migrations;
- managed secret store / key vault;
- Zendesk OAuth;
- webhook signing where supported;
- background retry queue;
- structured monitoring and alerting;
- configuration backup/rollback;
- approval workflow;
- asset inventory integration.

---

# 32. Implementation Rules

1. Treat this file as the source of truth.
2. Keep architecture simple and readable.
3. Do not remove Basic Auth.
4. Do not hardcode secrets or Zendesk IDs.
5. Do not commit `.env` files.
6. Keep Zendesk credentials server-side in environment variables.
7. Never return the Zendesk API token to the frontend.
8. Test credentials before using them.
9. Discovery and dry-run operations are read-only.
10. Require explicit confirmation before Zendesk mutation.
11. Bind approval to the exact reviewed plan fingerprint.
12. Re-read Zendesk before mutation and reject stale plans.
13. Create/reuse only exact Royal Tyres managed objects.
14. Never delete unrelated Zendesk configuration.
15. Verify objects after apply.
16. Store discovered/created IDs in SQL.
17. Commit the asset request before any Zendesk ticket call.
18. Zendesk failure must not lose the request.
19. Use SQLAlchemy and Pydantic.
20. Keep controllers thin and business logic in services.
21. Use React safe text rendering.
22. Never use `dangerouslySetInnerHTML`.
23. Keep `/health` public.
24. Keep Swagger available.
25. Run CI before merge.
26. Prefer understandable code over clever abstractions.

---

# 33. Definition of Done

Base application:

- [x] hosted frontend loads
- [x] Basic Auth works
- [x] form validation works
- [x] request persists to hosted SQL
- [x] audit event is created
- [x] request tracking works
- [x] Swagger works
- [x] Vercel can call Render through explicit CORS
- [x] CI exists

PR5:

- [ ] Render has `ZENDESK_SUBDOMAIN`
- [ ] Render has `ZENDESK_EMAIL`
- [ ] Render has `ZENDESK_API_TOKEN`
- [ ] Zendesk setup page loads
- [ ] backend env credentials can be tested
- [ ] browser never receives Zendesk credentials
- [ ] current Brand/Group/Fields/Form/View are discovered
- [ ] dry-run plan shows CREATE/REUSE
- [ ] plan fingerprint is generated
- [ ] Apply requires explicit confirmation
- [ ] stale approved plan is rejected
- [ ] Brand is created/reused
- [ ] Group is created/reused
- [ ] three custom fields are created/reused
- [ ] ticket form is created/reused
- [ ] view is created/reused
- [ ] all managed objects pass read-back verification
- [ ] managed object IDs persist in SQL
- [ ] new requests create tickets using those IDs
- [ ] Zendesk failure preserves the local request
- [ ] tests and CI pass

Later:

- [ ] webhook updates local Zendesk status
- [ ] invalid webhook secret is rejected
- [ ] manual Zendesk reconciliation works
- [ ] dashboard loads summary and sync health
- [ ] final README/demo documentation is complete

---

# 34. Final Principle

```text
Operational problem
        ↓
Clear requirement
        ↓
Simple architecture
        ↓
Validated input
        ↓
Durable persistence
        ↓
Server-side secrets
        ↓
Read-only discovery
        ↓
Human-approved plan
        ↓
Controlled external change
        ↓
Verification
        ↓
Auditability
        ↓
Recoverable failure
```

The goal is not to build the largest system. The goal is to build a **small system that works, is safe to operate, can be explained clearly, and demonstrates sound technical judgement**.
