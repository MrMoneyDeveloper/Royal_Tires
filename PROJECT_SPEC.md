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
8. safely configure the required Zendesk objects through an authenticated setup wizard;
9. create Zendesk tickets only after the local request is durably committed;
10. store the Zendesk ticket ID and sync state;
11. later support Zendesk webhook status updates and manual reconciliation;
12. provide an operations dashboard;
13. expose Swagger/OpenAPI;
14. use GitHub branches, pull requests and CI.

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
- Zendesk setup wizard
- Dashboard

**Controller**

- FastAPI route modules
- authenticate
- validate
- call services
- return HTTP responses

**Service layer**

- request creation
- Zendesk credential testing
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
| Integration governance | Connect → discover → dry run → confirm → apply → verify |

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

Successful submission shows:

- local request ID
- internal status
- Zendesk ticket ID when available
- Zendesk sync state
- link to request tracking

A Zendesk outage must never lose the local request.

## `/requests/:id`

Display:

- local request ID
- requester
- asset
- reason
- internal status
- Zendesk ticket ID
- Zendesk status
- last Zendesk sync
- created / updated timestamps

A later phase adds **Refresh from Zendesk**.

## `/zendesk-setup`

Authenticated administration page for connecting and configuring a Zendesk sandbox safely.

This page is part of PR5 and is a deliberate extension of the interview requirement.

## `/dashboard`

Later operations view containing:

- total requests
- status totals
- asset breakdown
- recent requests
- Zendesk sync failures
- last successful sync

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

Production discussion may reference Entra ID / OIDC / SSO as the next step, but it is outside this practical.

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

No raw user HTML is intentionally rendered.

## Secrets

Never commit:

- Basic Auth password
- database password
- Zendesk API token
- encryption key
- webhook secret

Never log request Authorization headers or Zendesk tokens.

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

Singleton configuration record for the demo portal.

```text
id
subdomain
api_email
encrypted_api_token
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

The API token must be encrypted before it is stored in SQL.

---

# 9. Zendesk Credential Architecture

**Do not store the Zendesk domain, email and API token directly as Render environment variables.**

The administrator enters them through the authenticated Zendesk setup page.

The backend retains only a server-side root secret in Render:

```env
CONFIG_ENCRYPTION_KEY=
```

Flow:

```text
Authenticated portal user
        ↓
Zendesk setup form
        ↓ HTTPS
POST /api/zendesk/connect
        ↓
GET Zendesk /api/v2/users/me.json
        ↓
Credentials accepted
        ↓
Encrypt API token server-side
        ↓
Store encrypted token + instance/user metadata in PostgreSQL
        ↓
Never return token to browser
```

Changing `CONFIG_ENCRYPTION_KEY` invalidates the stored encrypted token and requires reconnecting Zendesk.

---

# 10. Zendesk Safe Setup Workflow

This workflow is based on the configuration-management pattern already used in CX Experts Zendesk tooling:

```text
CONNECT
   ↓
TEST CREDENTIALS
   ↓
READ EXISTING CONFIGURATION
   ↓
BUILD DRY-RUN PLAN
   ↓
DISPLAY CREATE / REUSE ACTIONS
   ↓
EXPLICIT USER CONFIRMATION
   ↓
APPLY
   ↓
READ BACK
   ↓
VERIFY AFTER
```

**The connection test and dry run must not mutate Zendesk.**

The application should never blindly push configuration on login.

---

# 11. Zendesk Discovery

After credentials are validated, the backend reads current Zendesk configuration through the API.

Required discovery endpoints:

```text
GET /api/v2/users/me.json
GET /api/v2/brands.json
GET /api/v2/groups.json
GET /api/v2/ticket_fields.json
GET /api/v2/ticket_forms.json
GET /api/v2/views.json
```

Discovery should follow pagination where present.

Objects are matched by exact Royal Tyres names so repeated setup is idempotent.

Unrelated Zendesk configuration must not be deleted.

---

# 12. Required Zendesk Configuration

The setup wizard owns the following small configuration set.

## Brand

```text
Royal Tyres
```

If the exact brand already exists, reuse it.

If missing, create it with a sandbox-safe subdomain derived from the connected sandbox name.

## Group

```text
Royal Tyres | IT Service Desk
```

If present, reuse it. Otherwise create it.

## Custom ticket fields

### Asset Type

```text
RT | Asset Type
```

Type: dropdown

Values:

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

Type: dropdown

Value:

```text
Royal Tyres Asset Portal -> royal_tires_asset_portal
```

## Ticket form

```text
Royal Tyres | IT Asset Request
```

The form is agent-side for the demo and contains the three Royal Tyres custom fields.

Where supported, restrict the form to the Royal Tyres brand.

## View

```text
Royal Tyres | IT Asset Requests
```

The View should select tickets assigned to the Royal Tyres IT Service Desk group and carrying the portal tag.

The app does not assign a View directly to a ticket. Zendesk Views are filters over ticket conditions.

---

# 13. Dry-Run Plan

After connection, show a plan similar to:

```text
Zendesk connected ✓
Instance: digify7.zendesk.com
User: <connected admin>

Brand
CREATE   Royal Tyres

Group
CREATE   Royal Tyres | IT Service Desk

Ticket field
CREATE   RT | Asset Type

Ticket field
CREATE   RT | Local Request ID

Ticket field
CREATE   RT | Request Source

Ticket form
CREATE   Royal Tyres | IT Asset Request

View
CREATE   Royal Tyres | IT Asset Requests
```

If an exact object already exists:

```text
REUSE   #<zendesk-id>
```

No mutation occurs while this plan is displayed.

---

# 14. Explicit Apply Confirmation

The administrator must explicitly confirm before mutation.

Frontend wording should make the effect clear:

```text
I reviewed the dry-run plan. Create only the missing Royal Tyres configuration and do not delete unrelated Zendesk data.
```

API:

```text
POST /api/zendesk/apply
```

Body:

```json
{
  "confirm": true
}
```

The backend rejects the apply request if confirmation is false or absent.

The connected Zendesk user must be an admin for configuration creation.

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

The apply operation must:

- create only missing Royal Tyres objects;
- reuse exact existing Royal Tyres objects;
- never delete unrelated objects;
- avoid duplicate Royal Tyres objects when rerun;
- tolerate a partially completed prior run by rediscovering before each ensure operation.

A later hardening phase may add controlled UPDATE behaviour for exact portal-owned objects if required. It is not needed merely to demonstrate safe provisioning.

---

# 16. Verify After

After apply, read each resulting object back from Zendesk by ID.

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

Only after verification succeeds should the connection be considered configured.

Persist the verified Zendesk IDs in `zendesk_connection`.

---

# 17. Zendesk Setup API

All three endpoints require the portal Basic Auth.

## Status / plan

```text
GET /api/zendesk/setup
```

Returns:

- connection state
- connected instance
- connected Zendesk user summary
- whether the user can configure
- dry-run plan
- stored object IDs
- verification results where available

Never returns the Zendesk token.

## Connect

```text
POST /api/zendesk/connect
```

Request:

```json
{
  "subdomain": "digify7",
  "email": "admin@example.com",
  "api_token": "<secret>"
}
```

Actions:

1. normalise the domain/subdomain;
2. test `/users/me`;
3. encrypt the token;
4. store connection metadata;
5. discover current configuration;
6. return the dry-run plan.

No Zendesk configuration is changed.

## Apply

```text
POST /api/zendesk/apply
```

Requires explicit confirmation, creates/reuses managed configuration, reads it back and returns verification.

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

Only use IDs saved by the verified setup flow.

Ticket payload includes:

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

Example subject:

```text
IT Asset Request #27 - Laptop - Mohammed Farhaan Buckas
```

External ID:

```text
royal-tires-asset-27
```

Tags:

```text
it_asset_request
royal_tires_asset_portal
local_request_27
```

Custom fields:

```text
RT | Asset Type        = laptop
RT | Local Request ID  = 27
RT | Request Source    = royal_tires_asset_portal
```

Store returned Zendesk values:

```text
zendesk_ticket_id
zendesk_status
zendesk_sync_status = synced
zendesk_last_synced_at
```

On failure:

```text
zendesk_ticket_id = null
zendesk_sync_status = sync_failed
```

and preserve the local request.

---

# 20. Zendesk Webhook — Later PR

Primary future status-sync endpoint:

```text
POST /api/webhooks/zendesk
```

Use a shared secret for the interview version:

```env
ZENDESK_WEBHOOK_SECRET=
```

Expected flow:

```text
Zendesk ticket status changes
        ↓
Zendesk trigger
        ↓
Webhook to Render FastAPI
        ↓
Validate secret
        ↓
Locate local request
        ↓
Update Zendesk/local status fields
        ↓
Audit event
```

Do not expose the portal Basic Auth credentials to Zendesk.

---

# 21. Manual Reconciliation — Later PR

```text
POST /api/requests/{id}/sync
```

Use the stored encrypted Zendesk connection and ticket ID to read current Zendesk state and repair a missed webhook event.

Webhook = primary event-driven path.  
Manual sync = recovery path.

---

# 22. Core API Endpoints

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

Swagger remains available at:

```text
/docs
```

---

# 23. Logging

Technical logs may include:

```text
HTTP method
route
status code
request ID
event type
Zendesk operation result
```

Do not log:

```text
APP_PASSWORD
Authorization header
Zendesk API token
CONFIG_ENCRYPTION_KEY
webhook secret
```

The audit table remains separate from operational logs.

---

# 24. CORS

Hosted frontend and backend use different origins.

Current production origin:

```text
https://royal-tires.vercel.app
```

Current backend:

```text
https://royal-tires-api.onrender.com
```

`FRONTEND_URL` must explicitly allow production and local development origins.

Do not use wildcard CORS in the final demo.

---

# 25. Environment Variables

Backend:

```env
APP_USERNAME=
APP_PASSWORD=
DATABASE_URL=
FRONTEND_URL=
CONFIG_ENCRYPTION_KEY=
ZENDESK_WEBHOOK_SECRET=
```

**No Zendesk API token is required in Render environment variables.**

Zendesk credentials are entered through `/zendesk-setup` and encrypted server-side.

Frontend:

```env
VITE_API_URL=https://royal-tires-api.onrender.com
```

No server secret may be stored in a Vite environment variable.

---

# 26. Deployment State and Next Order

Base hosting is already established:

```text
Render PostgreSQL       ✓
Render FastAPI          ✓
Vercel React frontend   ✓
Hosted request create   ✓
Hosted request tracking ✓
```

Before merging the Zendesk setup branch:

1. add a long random `CONFIG_ENCRYPTION_KEY` to Render;
2. confirm PR5 CI passes;
3. merge PR5;
4. allow Render and Vercel auto-deploy;
5. sign into the portal;
6. open **Zendesk setup**;
7. enter sandbox domain/email/token;
8. Test & Connect;
9. inspect the dry-run plan;
10. explicitly confirm Apply;
11. verify all managed Zendesk objects return PASS;
12. create a new asset request;
13. confirm the real Zendesk ticket uses the correct brand, group, form and custom fields.

---

# 27. Git / Pull Request Sequence

Completed / current sequence:

```text
PR1  chore/project-scaffold       ✓
PR2  feat/core-request-api        ✓
PR3  feat/auth-security           ✓
PR4  feat/request-ui              ✓
PR5  feat/zendesk-integration     CURRENT / DRAFT
PR6  feat/zendesk-sync            later
PR7  feat/operations-dashboard    later
PR8  chore/deployment             mostly completed manually during build
PR9  chore/final-hardening        later
```

## PR5 — Zendesk Integration

PR5 now includes more than basic ticket creation.

Required PR5 scope:

- `zendesk_connection` SQL model;
- server-side token encryption;
- Zendesk Test & Connect flow;
- `/users/me` credential validation;
- current config discovery;
- dry-run CREATE / REUSE plan;
- explicit apply confirmation;
- idempotent Brand creation/reuse;
- idempotent Group creation/reuse;
- idempotent custom Field creation/reuse;
- idempotent Ticket Form creation/reuse;
- idempotent View creation/reuse;
- post-apply verification;
- persisted Zendesk IDs;
- ticket creation using those IDs;
- Zendesk failure isolation;
- tests;
- authenticated React Zendesk setup view.

Do not merge PR5 merely because the simple ticket-creation code works. Merge only when the setup workflow and tests are ready.

---

# 28. CI

GitHub Actions should run on pull requests and main.

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

# 29. Testing Requirements

Minimum important behaviours:

1. `/health` returns 200;
2. protected endpoints reject invalid Basic Auth;
3. valid asset request persists;
4. validation rejects invalid input;
5. SQL injection-like input remains harmless data;
6. React renders malicious-looking HTML as text;
7. Zendesk Connect validates `/users/me` before storing connection;
8. stored Zendesk token is encrypted, not plaintext;
9. Zendesk Connect does not mutate configuration;
10. Apply rejects missing/false confirmation;
11. Apply stores managed object IDs;
12. post-apply verification succeeds for created/reused objects;
13. ticket creation uses verified configuration IDs;
14. Zendesk ticket creation success stores ticket ID;
15. Zendesk failure preserves the local request;
16. later webhook secret validation;
17. later manual reconciliation;
18. frontend production build passes;
19. desktop/mobile browser tests pass.

---

# 30. Demo Scenario

## Demo A — Base request

Create an asset request and show:

```text
React validation
→ FastAPI
→ PostgreSQL
→ request ID
→ request tracking
```

## Demo B — Zendesk configuration governance

Show:

```text
Zendesk Setup
→ Test & Connect
→ connected admin identity
→ current config discovery
→ CREATE / REUSE dry-run plan
→ confirmation checkbox
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

This is a stronger demonstration than manually pasting object IDs into environment variables because the application discovers and governs its own small integration configuration.

## Demo C — Later two-way sync

Change Zendesk ticket status and demonstrate webhook/manual reconciliation once PR6 exists.

---

# 31. Interview Explanation

A useful concise explanation:

> PostgreSQL is the primary system of record, so the employee request is committed before any Zendesk call. Zendesk is treated as a secondary business-system integration. Instead of hardcoding sandbox IDs, the authenticated setup page tests the Zendesk login, discovers existing configuration, creates a dry-run plan, requires explicit confirmation, creates only missing Royal Tyres objects, verifies them after creation, and stores the resulting IDs. The API token is encrypted server-side and is never returned to the browser.

Trade-offs:

- Basic Auth is intentionally simple because it was explicitly requested.
- The app is monolithic because the scope does not justify microservices.
- Automatic retries/background jobs are deferred to avoid unnecessary infrastructure.
- Configuration UPDATE/rollback can be added later; PR5 initially manages CREATE/REUSE only for exact portal-owned names.
- The local database remains authoritative when Zendesk is unavailable.

---

# 32. Production Improvements

If this moved beyond the interview demo:

- Entra ID / OIDC / SSO;
- role-based admin permissions;
- formal database migrations such as Alembic;
- key management service rather than one Render secret;
- Zendesk OAuth instead of API-token auth;
- webhook signing where supported;
- background retry queue for sync failures;
- centralised structured logging and alerting;
- configuration backup/rollback;
- approval workflow;
- asset inventory integration.

---

# 33. Implementation Rules

1. Treat this file as the source of truth.
2. Keep architecture simple and readable.
3. Do not remove Basic Auth.
4. Do not hardcode secrets or Zendesk IDs.
5. Do not commit `.env` files.
6. Do not expose Zendesk API tokens to the frontend after submission.
7. Encrypt the token before storing it in SQL.
8. Test credentials before saving/using them.
9. Discovery and dry-run operations are read-only.
10. Require explicit confirmation before Zendesk configuration mutation.
11. Create/reuse only exact Royal Tyres managed objects.
12. Never delete unrelated Zendesk configuration.
13. Verify objects after apply.
14. Store discovered/created IDs in SQL.
15. Commit the asset request before any Zendesk ticket call.
16. Zendesk failure must not lose the request.
17. Use SQLAlchemy and Pydantic.
18. Keep controllers thin and business logic in services.
19. Use React safe text rendering.
20. Never use `dangerouslySetInnerHTML`.
21. Keep `/health` public.
22. Keep Swagger available.
23. Run CI before merge.
24. Prefer understandable code over clever abstractions.

---

# 34. Definition of Done

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

- [ ] Render has `CONFIG_ENCRYPTION_KEY`
- [ ] Zendesk setup page loads
- [ ] Zendesk credentials can be tested
- [ ] API token is encrypted in SQL
- [ ] current Brand/Group/Fields/Form/View are discovered
- [ ] dry-run plan shows CREATE/REUSE
- [ ] Apply requires explicit confirmation
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

# 35. Final Principle

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
Controlled external configuration
        ↓
Explicit confirmation
        ↓
Verified integration
        ↓
Auditability
        ↓
Recoverable failure
```

The goal is not to build the largest system.

The goal is to build a **small system that works, is safe to operate, can be explained clearly, and demonstrates sound technical judgement**.
