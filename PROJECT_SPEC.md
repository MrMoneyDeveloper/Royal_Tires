# IT Asset Request Tool — Technical Interview Project Specification

**Candidate:** Mohammed Farhaan Buckas  
**Purpose:** Royal Tyres technical interview practical  
**Hosting:** React/Vite on Vercel, FastAPI on Render, Render PostgreSQL, Zendesk sandbox  
**Design goal:** A small full-stack application that is easy to explain while demonstrating persistence, security, controlled Zendesk provisioning, notifications, auditability and recoverable integration failure.

---

# 1. Scope

Build an authenticated internal IT Asset Request Tool where an employee can request equipment such as a laptop, monitor, mouse, keyboard, headset, docking station or another item.

The hosted solution must:

1. provide a React form with frontend validation;
2. expose a FastAPI backend API;
3. persist requests in SQL;
4. protect business endpoints with Basic Auth;
5. use Pydantic and SQLAlchemy to avoid unsafe input handling and SQL interpolation;
6. render user data as normal React text and never use `dangerouslySetInnerHTML`;
7. keep technical logs plus a durable `audit_logs` table;
8. integrate with a real Zendesk sandbox;
9. keep Zendesk credentials and webhook secrets server-side in Render environment variables;
10. discover Zendesk configuration before changing it;
11. show a CREATE/REUSE dry-run plan and bind approval to its SHA-256 fingerprint;
12. provision the required Brand, Group, Fields, Form, View, notification target, webhook and triggers only after explicit approval;
13. create Zendesk tickets only after the local request is committed;
14. email demo notifications for new requests and status changes;
15. push Zendesk status changes back into PostgreSQL so **Track a request** reflects the agent-side status;
16. provide Swagger/OpenAPI;
17. use feature branches, pull requests and GitHub Actions CI.

Manual pull/reconciliation and the operations dashboard remain later enhancements. Do not add microservices, queues or infrastructure the practical does not need.

---

# 2. Hosted Architecture

```text
┌──────────────────────────────┐
│ React + Vite on Vercel       │
│ royal-tires.vercel.app       │
│                              │
│ Login                        │
│ New Request                  │
│ Track a Request              │
│ Zendesk Setup                │
└───────────────┬──────────────┘
                │ HTTPS / JSON / Basic Auth
                ▼
┌────────────────────────────────────────┐
│ FastAPI on Render                      │
│ royal-tires-api.onrender.com           │
│                                        │
│ Request controller/service             │
│ Zendesk setup controller/service       │
│ Zendesk webhook controller/service     │
│ Pydantic validation                    │
│ Audit logging                          │
│ Render-held secrets                    │
└──────────┬───────────────────┬─────────┘
           │                   │
           ▼                   ▼
┌─────────────────────┐   ┌──────────────────────────┐
│ Render PostgreSQL   │   │ Zendesk Sandbox          │
│                     │   │                          │
│ asset_requests      │   │ Brand / Group            │
│ audit_logs          │   │ Ticket Fields / Form     │
│ zendesk_connection  │   │ View                     │
└─────────────────────┘   │ Email Target             │
                          │ Webhook                  │
                          │ Triggers                 │
                          │ Tickets                  │
                          └────────────┬─────────────┘
                                       │ status changed
                                       ▼
                          POST /api/webhooks/zendesk
                                       │
                                       ▼
                              update PostgreSQL
                                       │
                                       ▼
                              Track a Request
```

Local development may use SQLite through the same SQLAlchemy models.

---

# 3. MVC / Layer Mapping

**Model**
- `AssetRequest`
- `AuditLog`
- `ZendeskConnection`
- SQLAlchemy

**View**
- React/Vite login
- asset request form
- request detail/tracking
- Zendesk configuration screen

**Controller**
- FastAPI request routes
- Zendesk setup routes
- Zendesk webhook route

**Services**
- request persistence
- Zendesk credential validation
- live configuration discovery
- dry-run planning
- configuration apply/verification
- ticket creation
- inbound status synchronization

Controllers stay thin. Business logic stays in services.

---

# 4. Security

## Portal authentication

The assignment explicitly requires Basic Auth.

```env
APP_USERNAME=
APP_PASSWORD=
```

The React application holds the demo credentials only in memory for the active browser session.

## SQL injection

Use SQLAlchemy ORM / parameterized queries. Never concatenate user-controlled text into SQL.

## XSS

Render requester names, reasons, statuses and other values as normal React text. Never use raw HTML rendering or `dangerouslySetInnerHTML`.

## Secrets

Never commit or return:

- `APP_PASSWORD`
- database password
- `ZENDESK_API_TOKEN`
- `ZENDESK_WEBHOOK_SECRET`

Never log Authorization headers, API tokens or webhook secrets.

The Zendesk webhook does **not** use the portal Basic Auth credentials. It uses its own bearer secret.

---

# 5. Environment Variables

Backend / Render:

```env
APP_USERNAME=
APP_PASSWORD=
DATABASE_URL=
FRONTEND_URL=

ZENDESK_SUBDOMAIN=
ZENDESK_EMAIL=
ZENDESK_API_TOKEN=
ZENDESK_WEBHOOK_SECRET=
ZENDESK_NOTIFICATION_EMAIL=farhaanhotd1@gmail.com
```

Render supplies the hosted callback origin through:

```env
RENDER_EXTERNAL_URL=
```

The application combines it with:

```text
/api/webhooks/zendesk
```

Frontend / Vercel:

```env
VITE_API_URL=https://royal-tires-api.onrender.com
```

No server secret belongs in a Vite environment variable.

---

# 6. Database

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

Important events:

```text
REQUEST_CREATED
ZENDESK_TICKET_CREATED
ZENDESK_CREATE_FAILED
ZENDESK_WEBHOOK_RECEIVED
ZENDESK_STATUS_CHANGED
```

## `zendesk_connection`

Stores verified safe metadata and the core Zendesk IDs used for ticket creation:

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

The Zendesk API token is **not** stored in PostgreSQL.

Workflow resources such as targets, webhooks and triggers are rediscovered by their exact managed names instead of requiring extra database columns.

---

# 7. Application Pages

## `/request`

Fields:

- requester name
- requester email
- asset type
- business reason

Allowed asset types:

```text
Laptop
Monitor
Mouse
Keyboard
Headset
Docking Station
Other
```

After submission, display the local request ID, local status, Zendesk ticket ID when present and Zendesk sync state.

## `/requests/:id`

Display:

- request ID
- requester
- asset type
- reason
- local status
- Zendesk ticket ID
- Zendesk status
- sync state
- last successful sync

The page includes **Refresh status** and also silently reads the local API every 10 seconds while open. Zendesk itself pushes status changes into PostgreSQL through the webhook, so the browser never needs Zendesk credentials.

## `/zendesk-setup`

Authenticated administration page that:

1. confirms server-side Zendesk variables exist;
2. tests the environment credentials;
3. discovers live Zendesk resources;
4. displays the complete configuration/workflow plan;
5. shows CREATE or REUSE for every managed object;
6. fingerprints the exact plan;
7. requires explicit approval;
8. re-reads Zendesk before mutation;
9. refuses stale approved plans;
10. creates/reuses resources in dependency order;
11. verifies every created/reused resource afterward.

---

# 8. Governed Zendesk Setup

The control pattern intentionally follows the proven CX Experts / AI Site Factory approach: inspect first, stage the intended external changes, require a human gate, then execute and verify.

```text
Render ENV credentials
        ↓
Test connection
        ↓
GET /api/v2/users/me.json
        ↓
Discover current Zendesk state
        ↓
Build CREATE / REUSE plan
        ↓
SHA-256 fingerprint
        ↓
Human reviews exact plan
        ↓
Human approves
        ↓
Re-read Zendesk
        ↓
Plan fingerprint still matches?
   ├─ NO → HTTP 409, refresh and review again
   └─ YES
        ↓
Validate / create resources
        ↓
Read resources back
        ↓
PASS / FAIL verification
```

Connection testing and discovery are read-only.

No configuration or trigger is pushed merely because the user logged in or clicked **Test environment connection**.

---

# 9. Zendesk Discovery

Discovery includes:

```text
GET /api/v2/users/me.json
GET /api/v2/brands.json
GET /api/v2/groups.json
GET /api/v2/ticket_fields.json
GET /api/v2/ticket_forms.json
GET /api/v2/views.json
GET /api/v2/targets
GET /api/v2/webhooks
GET /api/v2/triggers.json
```

Managed objects are identified by exact Royal Tyres names. Re-running setup therefore produces REUSE actions for resources already created during a prior or partially failed run.

Unrelated Zendesk configuration is never deleted.

---

# 10. Managed Zendesk Resources

## Core ticket configuration

```text
Brand
Royal Tyres

Group
Royal Tyres | IT Service Desk

Ticket Field
RT | Asset Type
API type: tagger
Options: laptop, monitor, mouse, keyboard, headset, docking_station, other

Ticket Field
RT | Local Request ID
API type: text

Ticket Field
RT | Request Source
API type: tagger
Value: royal_tires_asset_portal

Ticket Form
Royal Tyres | IT Asset Request

View
Royal Tyres | IT Asset Requests
```

The View filters tickets assigned to the Royal Tyres IT Service Desk Group and tagged `royal_tires_asset_portal`.

## Demo notification target

```text
Email Target
Royal Tyres | Demo Notifications

Receiver
farhaanhotd1@gmail.com
```

The receiver is configurable through `ZENDESK_NOTIFICATION_EMAIL` but defaults to the demo address above.

## Status callback webhook

```text
Webhook
Royal Tyres | Asset Status Sync

Method
POST

Format
JSON

Destination
${RENDER_EXTERNAL_URL}/api/webhooks/zendesk

Authentication
Bearer ZENDESK_WEBHOOK_SECRET
```

The webhook is attached to ticket activity through a trigger rather than subscribing directly to a predefined ticket-event payload. This lets the trigger send the small payload the FastAPI endpoint expects.

## Triggers

### `Royal Tyres | Notify Demo Receiver - New Request`

Conditions:

```text
current_tags includes royal_tires_asset_portal
update_type = Create
```

Action:

```text
notification_target → Royal Tyres | Demo Notifications
```

Purpose: demonstrate an email arriving when the portal creates a Zendesk ticket.

### `Royal Tyres | Notify Demo Receiver - Status Update`

Conditions:

```text
current_tags includes royal_tires_asset_portal
update_type = Change
status changed
```

Action:

```text
notification_target → Royal Tyres | Demo Notifications
```

Purpose: demonstrate email notification after an agent changes status.

### `Royal Tyres | Sync Status to Asset Portal`

Conditions:

```text
current_tags includes royal_tires_asset_portal
update_type = Change
status changed
```

Action:

```text
notification_webhook → Royal Tyres | Asset Status Sync
```

Payload template:

```json
{
  "event": "status_changed",
  "ticket_id": "{{ticket.id}}",
  "external_id": "{{ticket.external_id}}",
  "status": "{{ticket.status}}"
}
```

Purpose: make the Zendesk agent-side status visible in **Track a request**.

---

# 11. Dry-Run Plan

Before any mutation, the configuration page should show the complete plan, including workflow resources:

```text
Brand         CREATE / REUSE  Royal Tyres
Group         CREATE / REUSE  Royal Tyres | IT Service Desk
Ticket field  CREATE / REUSE  RT | Asset Type
Ticket field  CREATE / REUSE  RT | Local Request ID
Ticket field  CREATE / REUSE  RT | Request Source
Ticket form   CREATE / REUSE  Royal Tyres | IT Asset Request
View          CREATE / REUSE  Royal Tyres | IT Asset Requests
Email target  CREATE / REUSE  Royal Tyres | Demo Notifications
Webhook       CREATE / REUSE  Royal Tyres | Asset Status Sync
Trigger       CREATE / REUSE  Royal Tyres | Notify Demo Receiver - New Request
Trigger       CREATE / REUSE  Royal Tyres | Notify Demo Receiver - Status Update
Trigger       CREATE / REUSE  Royal Tyres | Sync Status to Asset Portal
```

The email-target row shows the configured demo receiver. The webhook and trigger rows explain their purpose without exposing secrets.

---

# 12. Apply Rules and Dependency Order

The administrator must tick the explicit approval checkbox and submit the exact reviewed plan fingerprint.

Immediately before mutation, FastAPI rebuilds the plan. If the fingerprint changed, return HTTP 409 and require review again.

Apply order:

```text
Brand
  ↓
Group
  ↓
3 Ticket Fields
  ↓
Ticket Form
  ↓
View
  ↓
Email Target
  ↓
Webhook
  ↓
Validate Trigger definitions
  ↓
3 active Triggers
```

The trigger definitions are validated through Zendesk before creation.

Unlike the larger AI Site Factory provisioning flow, which kept core triggers inactive for a separate activation stage, this interview implementation creates the three demo triggers **active only after the administrator has already passed the fingerprinted human approval gate**. That preserves the safety principle while eliminating a second manual Admin Center step during the demo.

Every ensure operation re-reads Zendesk and reuses an exact existing object before attempting a create. This makes a retry safe after a partial failure.

---

# 13. Verify After

After Apply, read all managed resources back and show PASS / FAIL:

```text
Brand
Group
Asset Type field
Local Request ID field
Request Source field
Ticket Form
View
Email Target
Webhook
New Request Email Trigger
Status Update Email Trigger
Status Sync Trigger
```

Only after the complete apply succeeds are the core ticket-creation IDs marked configured locally.

---

# 14. Request Creation and Failure Isolation

The local database is the primary system of record.

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
COMMIT PostgreSQL
        ↓
Create Zendesk ticket using verified IDs
        ↓
 success                   failure
    │                          │
    ▼                          ▼
store ticket ID          keep local request
sync status              mark sync_failed
    │                          │
    └────────────┬─────────────┘
                 ▼
             commit again
```

Zendesk failure must never roll back the employee's saved request.

---

# 15. Zendesk Ticket Payload

Each ticket includes:

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

Example linkage:

```text
Subject: IT Asset Request #27 - Laptop - Mohammed Farhaan Buckas
External ID: royal-tires-asset-27
Tags: it_asset_request, royal_tires_asset_portal, local_request_27
RT | Asset Type = laptop
RT | Local Request ID = 27
RT | Request Source = royal_tires_asset_portal
```

Returned Zendesk values populate:

```text
zendesk_ticket_id
zendesk_status
zendesk_sync_status
zendesk_last_synced_at
```

---

# 16. Zendesk → Portal Status Sync

FastAPI exposes:

```text
POST /api/webhooks/zendesk
```

This endpoint deliberately does not require the user's portal Basic Auth credentials. Instead it requires:

```text
Authorization: Bearer <ZENDESK_WEBHOOK_SECRET>
```

Expected JSON:

```json
{
  "event": "status_changed",
  "ticket_id": 12345,
  "external_id": "royal-tires-asset-27",
  "status": "pending"
}
```

Processing:

```text
Validate bearer secret
        ↓
Find asset request by zendesk_ticket_id
        ↓
If external_id supplied, verify it matches local request identity
        ↓
Update local status + zendesk_status
        ↓
Set zendesk_sync_status = synced
        ↓
Set zendesk_last_synced_at
        ↓
Write audit event
        ↓
Commit
```

Duplicate status callbacks are accepted idempotently and logged as received rather than treated as a second status change.

The tracking page reads only FastAPI/PostgreSQL, so no Zendesk credential is exposed to the browser.

---

# 17. API Endpoints

```text
GET  /health

POST /api/requests
GET  /api/requests
GET  /api/requests/{id}

GET  /api/zendesk/setup
POST /api/zendesk/connect
POST /api/zendesk/apply

POST /api/webhooks/zendesk

POST /api/requests/{id}/sync        # later manual reconciliation
GET  /api/dashboard/summary         # later dashboard
```

Swagger/OpenAPI remains available at `/docs`.

---

# 18. Logging and Auditability

Technical logs may contain method, route, status code, local request ID, Zendesk ticket ID and event result.

They must not contain credentials or secrets.

The durable audit table records meaningful business/integration events independently from application logs.

---

# 19. Git / Pull Request History

Actual repository progression:

```text
PR1  chore/project-scaffold                         ✓
PR2  feat/core-request-api                          ✓
PR3  feat/auth-security                             ✓
PR4  feat/request-ui                                ✓
PR5  feat/zendesk-integration                       ✓
PR6  fix/zendesk-field-types                        ✓
PR7  feat/zendesk-workflow-sync                     CURRENT
```

PR6 corrected the live Zendesk API values used for single-select fields and the View subject column.

PR7 adds:

- demo email target;
- default notification receiver;
- Zendesk webhook;
- new-request email trigger;
- status-change email trigger;
- status-change portal-sync trigger;
- FastAPI webhook authentication and persistence;
- request tracking refresh/polling;
- tests for provisioning and callbacks.

Dashboard and manual pull reconciliation follow only if time remains.

---

# 20. CI Requirements

GitHub Actions runs on PRs and `main`.

Backend:

```text
install dependencies
pytest
```

Frontend:

```text
npm ci
unit tests
Vite build
Playwright Chromium tests
```

Do not merge a failing PR.

Important PR7 tests include:

- webhook rejects missing/wrong bearer token;
- valid callback updates the local request;
- duplicate callback is idempotent;
- external-ID mismatch is rejected;
- dry-run includes email target, webhook and three triggers;
- trigger templates use Zendesk Create/Change semantics;
- webhook provisioning uses the Render callback URL and bearer secret;
- frontend setup view displays workflow resources and receiver;
- request tracking remains functional.

---

# 21. Live Demo Sequence

```text
1. Log into Royal Tyres portal.
2. Open Zendesk Setup.
3. Test environment connection.
4. Show live CREATE / REUSE plan.
5. Point out Brand, Group, Fields, Form, View, Email Target, Webhook and Triggers.
6. Show the notification receiver.
7. Approve the exact fingerprinted plan.
8. Apply and show PASS verification.
9. Submit a new Laptop request.
10. Show local request ID and real Zendesk ticket ID.
11. Show notification email arriving.
12. Open the Zendesk ticket.
13. Change ticket status, for example New → Pending.
14. Show status-update email arriving.
15. Return to Track a Request.
16. Within the polling interval, show local status = Pending and sync timestamp updated.
17. Explain that the webhook updated PostgreSQL; the browser did not call Zendesk directly.
```

This demonstrates both outbound integration and inbound event synchronization without bloating the architecture.

---

# 22. Interview Explanation

> PostgreSQL is the primary system of record, so the employee request is committed before any Zendesk call. Zendesk credentials stay only in the Render backend environment. The setup screen discovers the live Zendesk instance and produces a CREATE/REUSE dry-run plan covering both ticket configuration and workflow resources. The exact plan is fingerprinted and must be explicitly approved. The backend re-reads Zendesk immediately before applying it, validates trigger definitions, creates only missing Royal Tyres resources, and verifies them afterward. Once active, new portal requests create Zendesk tickets and send a demo email. Zendesk status changes trigger an authenticated webhook back to FastAPI, which updates PostgreSQL so the Track a Request page reflects the agent-side status.

Trade-offs:

- Basic Auth is intentionally simple because the assignment explicitly requires it.
- A separate webhook bearer secret avoids exposing portal credentials to Zendesk.
- The application stays monolithic because the scope does not justify microservices.
- The local database remains authoritative when Zendesk is unavailable.
- Background queues/retries and a manual reconciliation endpoint are sensible production follow-ups but are not required for the live demo.

---

# 23. Definition of Done

Base application:

- [x] hosted React frontend
- [x] hosted FastAPI backend
- [x] hosted PostgreSQL persistence
- [x] Basic Auth
- [x] frontend/backend validation
- [x] request tracking
- [x] audit logging
- [x] Swagger
- [x] CI

Core Zendesk integration:

- [x] server-side Zendesk credentials
- [x] environment connection test
- [x] live config discovery
- [x] CREATE/REUSE dry run
- [x] SHA-256 reviewed-plan fingerprint
- [x] explicit approval gate
- [x] stale-plan rejection
- [x] Brand/Group/Fields/Form/View provisioning logic
- [x] ticket-creation logic
- [x] local persistence before Zendesk

PR7 workflow integration:

- [x] default demo email receiver in configuration
- [x] Email Target provisioning logic
- [x] Webhook provisioning logic
- [x] new-request email Trigger template
- [x] status-change email Trigger template
- [x] status-sync Trigger template
- [x] FastAPI bearer-authenticated webhook endpoint
- [x] local status/audit update logic
- [x] tracking page refresh/polling
- [ ] PR7 GitHub CI green
- [ ] `ZENDESK_WEBHOOK_SECRET` configured in Render
- [ ] refreshed live dry-run reviewed
- [ ] full Zendesk apply verified
- [ ] new-request email live-tested
- [ ] Zendesk status → portal sync live-tested

Later if time remains:

- [ ] manual Zendesk reconciliation endpoint
- [ ] operations dashboard
- [ ] final presentation/demo hardening

---

# 24. Final Principle

```text
Validate
   ↓
Persist locally
   ↓
Discover external state
   ↓
Show exact plan
   ↓
Human approves
   ↓
Validate external rules
   ↓
Apply controlled changes
   ↓
Verify
   ↓
Observe events
   ↓
Synchronize safely
   ↓
Audit everything important
```

The goal is not the largest system. The goal is a **small, demonstrably reliable integration that can be explained under questioning**.
