# IT Asset Request Tool — Technical Interview Project Specification

**Candidate:** Mohammed Farhaan Buckas  
**Purpose:** Royal Tyres technical interview practical  
**Hosting:** React/Vite on Render Static Sites, FastAPI on Render, Render PostgreSQL, Zendesk sandbox
**Design goal:** A small full-stack application that is easy to explain while demonstrating persistence, security, controlled Zendesk provisioning, notifications, auditability, recoverable integration failure, and a clear MVC-style solution map.

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
17. use feature branches, pull requests and GitHub Actions CI;
18. keep the solution organized around an MVC mental model so every file has an obvious responsibility.

Manual pull/reconciliation remains a later enhancement. The searchable operations dashboard is part of the hosted solution. Do not add microservices, queues or infrastructure the practical does not need.

---

# 2. Architecture Mental Model

The project deliberately uses a familiar MVC-style mental model even though the implementation is split between React and FastAPI.

```text
USER
 │
 ▼
VIEW
React page / shared layout / partial component
 │
 │ HTTPS / JSON
 ▼
CONTROLLER
FastAPI endpoint
 │
 ▼
SERVICE
Business use case / orchestration
 │
 ├──────────────► EXTERNAL INTEGRATION
 │                Zendesk
 │
 ▼
REPOSITORY
Database operations
 │
 ▼
MODEL
SQLAlchemy entities
 │
 ▼
DB CONTEXT
SQLAlchemy engine / session / transaction boundary
 │
 ▼
POSTGRESQL
```

Supporting layers:

```text
Schemas / DTOs / ViewModels
    define request and response contracts

Middleware
    applies cross-cutting behavior around HTTP requests

Helpers
    contain small reusable pure utilities

Core
    configuration, authentication, logging and application-wide setup

Shared Views / Partial Views
    reusable React layout and UI components
```

The core request lifecycle to remember is:

```text
View → Controller → Service → Repository → Model → DbContext → Database
```

The response returns in the opposite direction.

---

# 3. ASP.NET MVC Concept Mapping

The solution uses Python and React, but the architecture is intentionally mapped to familiar ASP.NET MVC concepts.

| Familiar concept | This project |
|---|---|
| Model | SQLAlchemy models in `backend/app/models/` |
| View | React page components in `frontend/src/views/` |
| Shared View / Layout | reusable React shell/layout components |
| Partial View | smaller reusable React components |
| Controller | FastAPI routers in `backend/app/controllers/` |
| Service | business logic in `backend/app/services/` |
| Repository | SQLAlchemy data access in `backend/app/repositories/` |
| DbContext | `backend/app/data/` (`base.py`, `db_context.py`, `session.py`) |
| ViewModel / DTO | Pydantic schemas in `backend/app/schemas/` |
| Middleware | FastAPI/CORS/request middleware around the controller pipeline |
| Helpers | small reusable formatting/validation/integration utilities |
| appsettings.json | Pydantic `Settings` + Render environment variables |
| Dependency Injection | FastAPI `Depends()` and scoped database sessions |

The names are a mental bridge. The implementation still follows the conventions of FastAPI, SQLAlchemy and React.

---

# 4. Current Physical Repository Map

This is the **actual current code layout** after the MVC physical-structure refactor.

```text
Royal_Tires/
│
├── PROJECT_SPEC.md
├── README.md
├── .github/workflows/ci.yml
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── controllers/
│   │   │   ├── request_controller.py
│   │   │   ├── zendesk_controller.py
│   │   │   └── webhook_controller.py
│   │   ├── services/
│   │   │   ├── request_service.py
│   │   │   ├── zendesk_service.py
│   │   │   ├── webhook_service.py
│   │   │   └── legacy_trigger_guard.py
│   │   ├── repositories/
│   │   │   ├── request_repository.py
│   │   │   ├── audit_repository.py
│   │   │   └── zendesk_repository.py
│   │   ├── models/
│   │   │   ├── asset_request.py
│   │   │   ├── audit_log.py
│   │   │   └── zendesk_connection.py
│   │   ├── schemas/
│   │   │   ├── request_schema.py
│   │   │   ├── zendesk_schema.py
│   │   │   └── webhook_schema.py
│   │   ├── data/
│   │   │   ├── base.py
│   │   │   ├── db_context.py
│   │   │   └── session.py
│   │   ├── middleware/
│   │   │   ├── request_logging.py
│   │   │   └── security_headers.py
│   │   ├── helpers/
│   │   │   └── request_identity.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── security.py
│   │       └── logging_config.py
│   └── tests/
│
└── frontend/
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── views/
    │   │   ├── RequestView.jsx
    │   │   ├── DashboardView.jsx
    │   │   ├── RequestDetailView.jsx
    │   │   ├── SettingsView.jsx
    │   │   └── ZendeskSetupView.jsx
    │   ├── layouts/
    │   │   ├── AppLayout.jsx
    │   │   └── AuthLayout.jsx
    │   ├── components/
    │   │   ├── shared/
    │   │   │   ├── Brand.jsx
    │   │   │   ├── Sidebar.jsx
    │   │   │   ├── Topbar.jsx
    │   │   │   └── Footer.jsx
    │   │   ├── AppLink.jsx
    │   │   ├── AssetRequestForm.jsx
    │   │   ├── StatusBadge.jsx
    │   │   └── SyncStatePanel.jsx
    │   ├── services/api.js
    │   └── helpers/
    │       ├── formatting.js
    │       └── validation.js
    └── tests/
```

The physical folders now match the MVC mental model. There are no compatibility facade modules for the retired root `repository.py`, `schemas.py` or `database.py` locations.

---

# 5. Model Layer

**Purpose:** represent persisted business data and database relationships.

Current physical location:

```text
backend/app/models/
```

Current Models:

## `asset_request.py`

Represents one employee asset request.

Conceptually:

```text
AssetRequest Model
```

Important persisted fields:

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

## `audit_log.py`

Represents durable business/integration audit events.

Conceptually:

```text
AuditLog Model
```

Important events include:

```text
REQUEST_CREATED
ZENDESK_TICKET_CREATED
ZENDESK_CREATE_FAILED
ZENDESK_WEBHOOK_RECEIVED
ZENDESK_STATUS_CHANGED
```

## `zendesk_connection.py`

Represents safe Zendesk connection metadata and verified configuration IDs.

It stores metadata such as:

```text
subdomain
api_email
connected Zendesk user details
brand_id
group_id
ticket_form_id
asset_type_field_id
local_request_id_field_id
request_source_field_id
view_id
connected/configured/verified timestamps
```

The Zendesk API token is **not** stored in this Model. It remains in Render environment variables.

### Model rule

Models describe persisted state. Models should not contain HTTP endpoint logic, Zendesk API calls, UI rendering or unrelated orchestration.

---

# 6. View Layer

**Purpose:** display information to the user and collect user input.

Current physical location:

```text
frontend/src/views/
```

Current page-level Views:

## `RequestView.jsx`

Conceptual MVC View:

```text
New Asset Request View
```

Responsibilities:

- display the new-request page;
- render the request form;
- submit through the frontend API service;
- display success/failure state;
- navigate to request tracking.

## `DashboardView.jsx`

Conceptual MVC View:

```text
IT Service Desk Dashboard View
```

Responsibilities:

- list and search local requests;
- filter active, solved and sync-failed records;
- show linked Zendesk ticket/status information;
- navigate to one request for detailed tracking.

## `SettingsView.jsx`

Conceptual MVC View:

```text
Application Settings View
```

Responsibilities:

- show account/session context;
- expose API diagnostics/Swagger navigation;
- host the governed Zendesk configuration View.

## `RequestDetailView.jsx`

Conceptual MVC View:

```text
Track a Request View
```

Responsibilities:

- display one local request;
- show Zendesk ticket and sync information;
- allow manual refresh of local status;
- poll the local API periodically while open.

This View never needs Zendesk credentials.

## `ZendeskSetupView.jsx`

Conceptual MVC View:

```text
Zendesk Configuration View
```

Responsibilities:

- show environment readiness;
- initiate read-only Zendesk connection testing;
- display CREATE/REUSE planning;
- display plan fingerprint information;
- capture explicit configuration approval;
- display PASS/FAIL verification after apply.

The View never receives the Zendesk API token or webhook secret.

---

# 7. Shared Views and Partial Views

React does not use Razor Partial Views, but reusable React components serve the same mental purpose.

## Current Partial View equivalents

Current physical location:

```text
frontend/src/components/
```

### `AssetRequestForm.jsx`

Conceptual mapping:

```text
Partial View: Asset Request Form
```

It owns the reusable form UI and frontend validation behavior.

### `StatusBadge.jsx`

Conceptual mapping:

```text
Partial View: Request Status Badge
```

It presents request/sync status consistently.

### `AppLink.jsx`

Conceptual mapping:

```text
Shared Partial: Application Navigation Link
```

It centralizes internal SPA navigation behavior.

## Shared View / Layout structure

The application shell is physically separated into real shared Views and Partial Views:

```text
frontend/src/layouts/
    AppLayout.jsx
    AuthLayout.jsx

frontend/src/components/shared/
    Brand.jsx
    Sidebar.jsx
    Topbar.jsx
    Footer.jsx
```

`App.jsx` owns routing and session composition. The layout files own the authenticated and unauthenticated shells, while shared components own reusable brand/navigation/footer presentation.

---

# 8. Controller Layer

**Purpose:** own HTTP routes and translate HTTP input/output into service calls.

Current physical location:

```text
backend/app/controllers/
```

## `request_controller.py`

Conceptual MVC Controller:

```text
RequestController
```

Responsibilities:

```text
POST /api/requests
GET  /api/requests
GET  /api/requests/{id}
```

Controller responsibilities should remain:

```text
receive HTTP request
apply authentication dependency
accept validated schema
call service
return HTTP response
```

It should not contain SQL queries or Zendesk workflow logic.

## `zendesk_controller.py`

Conceptual MVC Controller:

```text
ZendeskController
```

Responsibilities:

```text
GET  /api/zendesk/setup
POST /api/zendesk/connect
POST /api/zendesk/apply
```

It controls the setup HTTP boundary while `zendesk_service.py` performs the actual integration work.

## `webhook_controller.py`

Conceptual MVC Controller:

```text
WebhookController
```

Responsibilities:

```text
POST /api/webhooks/zendesk
```

It validates the inbound webhook boundary and delegates status synchronization to the webhook service.

### Controller rule

Controllers should stay thin.

A useful test is:

```text
If a controller starts deciding business workflow, calling SQL directly,
or implementing Zendesk payload rules, move that work into a Service.
```

---

# 9. Service Layer

**Purpose:** own business use cases, sequencing and orchestration.

Current physical location:

```text
backend/app/services/
```

## `request_service.py`

Conceptual service:

```text
RequestService
```

Responsibilities:

- create the local request;
- create its audit event;
- commit primary persistence before Zendesk;
- request Zendesk ticket creation;
- update local Zendesk sync information;
- preserve the request if Zendesk fails.

## `zendesk_service.py`

Conceptual service:

```text
ZendeskService
```

Responsibilities:

- validate environment-held Zendesk credentials;
- discover live Zendesk configuration;
- build the dry-run plan;
- create/reuse managed configuration;
- validate trigger definitions;
- verify created/reused objects;
- construct and submit Zendesk ticket payloads;
- keep secrets server-side.

This is the current external-integration service and is intentionally separate from request controllers.

## `webhook_service.py`

Conceptual service:

```text
WebhookService
```

Responsibilities:

- process validated Zendesk callback data;
- find the linked local request;
- validate its external ID relationship;
- update local/Zendesk status fields;
- keep duplicate callbacks idempotent;
- write audit events.

### Service rule

Services own **why and in what order** operations happen.

Controllers own HTTP. Repositories own SQL. Models own persisted state.

---

# 10. Repository Layer

**Purpose:** isolate database access from business orchestration.

Current physical location:

```text
backend/app/repositories/
```

Conceptual mapping:

```text
Repository layer
```

Typical responsibilities:

```text
create AssetRequest
get AssetRequest by ID
list AssetRequests
find by Zendesk ticket ID
add AuditLog
persist safe Zendesk configuration metadata
```

Current repository organization:

```text
backend/app/repositories/
    request_repository.py
    audit_repository.py
    zendesk_repository.py
```

A Repository should not decide whether a Zendesk call occurs before or after a database commit. That decision belongs to the Service layer.

---

# 11. DbContext / Data Layer

The project is not using Entity Framework Core, so there is no literal EF `DbContext` class.

For the MVC mental model, the SQLAlchemy **DbContext equivalent** is physically split by responsibility:

```text
backend/app/data/base.py
backend/app/data/db_context.py
backend/app/data/session.py
```

It owns:

```text
Declarative Base
SQLAlchemy engine creation
SQLite/PostgreSQL URL handling
connection options
scoped Session creation
get_db() dependency
transaction/session lifetime
UTC database timestamp behavior
```

The application also creates `session_factory` during app startup and exposes scoped sessions through FastAPI dependency injection.

Conceptual mapping:

```text
ASP.NET ApplicationDbContext
        ↓
SQLAlchemy engine + Base + Session factory + get_db()
```

The physical data package separates declarative/timestamp concerns, engine configuration and scoped session dependencies without introducing an artificial EF-style class.

The name `DbContext` may be used in documentation as a teaching/mental-model alias, but the implementation remains standard SQLAlchemy.

---

# 12. Schemas / DTOs / ViewModels

**Purpose:** define the shape and validation rules of data crossing HTTP/service boundaries.

Current physical location:

```text
backend/app/schemas/
```

Conceptual mapping:

```text
Pydantic Schema
    = DTO / Request Model / Response Model / ViewModel boundary
```

Examples include:

```text
AssetRequestCreate
AssetRequestResponse
ZendeskApplyRequest
ZendeskSetupStatus
webhook request/response structures
```

Schemas should own validation such as:

- required fields;
- email format;
- allowed asset types;
- field lengths;
- unexpected input rejection;
- API response shape.

Current schema organization:

```text
backend/app/schemas/
    request_schema.py
    zendesk_schema.py
    webhook_schema.py
```

---

# 13. Middleware Layer

**Purpose:** handle cross-cutting HTTP behavior that applies around Controllers rather than inside individual business use cases.

Current middleware is physically isolated in:

```text
backend/app/middleware/request_logging.py
backend/app/middleware/security_headers.py
```

Current cross-cutting responsibilities include:

- CORS configuration;
- request method/route/status logging;
- `X-Content-Type-Options: nosniff`;
- `Cache-Control: no-store` for API responses;
- safe global validation/exception handling.

Conceptual request pipeline:

```text
HTTP Request
    ↓
Middleware / CORS / security headers
    ↓
Controller
    ↓
Service
    ↓
Repository / Integration
    ↓
Controller Response
    ↓
Middleware
    ↓
HTTP Response
```

Current middleware organization:

```text
backend/app/middleware/
    request_logging.py
    security_headers.py
```

Middleware must not contain request-specific business workflow such as asset creation or Zendesk provisioning.

---

# 14. Helpers

**Purpose:** hold small reusable utilities that do not deserve their own Service and do not own business workflow.

Dedicated helper folders now contain small reusable pure utilities without owning business workflow.

Future examples:

```text
backend/app/helpers/
    datetime_helper.py
    zendesk_helper.py
    validation_helper.py

frontend/src/helpers/
    formatting.js
    validation.js
```

Good Helper examples:

```text
normalize a Zendesk subdomain
map Laptop → rt_asset_laptop field value
format a timestamp for display
build a stable external ID string
```

Bad Helper examples:

```text
create an entire Zendesk setup
save an asset request
synchronize a ticket status
```

Those are Services because they represent business use cases.

---

# 15. Core Layer

**Purpose:** hold application-wide infrastructure concerns.

Current physical location:

```text
backend/app/core/
```

## `config.py`

Conceptual role:

```text
Application Settings / appsettings equivalent
```

Reads environment variables and exposes safe typed settings.

## `security.py`

Conceptual role:

```text
Authentication / authorization infrastructure
```

Implements Basic Auth credential checking and security dependencies.

## `logging_config.py`

Conceptual role:

```text
Application logging configuration
```

Core should not contain request or Zendesk business workflow.

---

# 16. Frontend Service Layer

Current physical location:

```text
frontend/src/services/api.js
```

Conceptual role:

```text
ApiService / HTTP client
```

It owns browser-to-FastAPI communication such as:

```text
list requests
get request
create request
read Zendesk setup status
test Zendesk environment connection
apply approved Zendesk plan
```

React Views call this frontend Service rather than scattering raw `fetch()` calls across page components.

---

# 17. Application Entry Point / Composition Root

## Backend

```text
backend/app/main.py
```

Conceptual role:

```text
Application startup / composition root
```

It should primarily:

- create FastAPI;
- create/configure the database engine;
- register middleware;
- register Controllers/routers;
- register exception handlers;
- expose health endpoint;
- configure app-level dependencies/state.

Business workflow should remain outside `main.py`.

## Frontend

```text
frontend/src/main.jsx
frontend/src/App.jsx
```

`main.jsx` bootstraps React.

`App.jsx` owns routing/session composition. `AppLayout.jsx` and `AuthLayout.jsx` own the shared shells, while `components/shared/` contains reusable navigation, brand and footer partials.

---

# 18. SOLID Principles Applied to This Project

SOLID is used as a practical design guide rather than as interview vocabulary pasted over the codebase.

## S — Single Responsibility Principle

Each layer has one clear reason to change:

```text
View        → UI/display changes
Controller  → HTTP route/boundary changes
Service     → business workflow changes
Repository  → database access changes
Model       → persisted entity changes
DbContext   → database/session configuration changes
Schema      → API contract/validation changes
Middleware  → cross-cutting HTTP behavior changes
Helper      → small reusable utility changes
Core        → app-wide configuration/security/logging changes
```

Examples:

- changing the Zendesk ticket payload belongs in `ZendeskService`, not `RequestController`;
- changing SQL lookup behavior belongs in the Repository, not the React View;
- changing page presentation belongs in a View/Partial View, not a Model.

## O — Open/Closed Principle

The application should allow extension without rewriting unrelated layers.

Examples:

- adding another notification workflow should not require rewriting the request Controller;
- adding another asset option should flow through validation/mapping without changing database infrastructure;
- a future ServiceNow integration could be added through another integration Service instead of mixing ServiceNow code into Zendesk controllers.

## L — Liskov Substitution Principle

The current project does not rely heavily on inheritance, so this principle is intentionally lightweight.

If repository or integration interfaces are introduced later, replacements must preserve the expected contract.

Example:

```text
PostgreSQL request repository
and a test/in-memory repository
must both satisfy the same service expectations.
```

Do not invent inheritance purely to demonstrate this principle.

## I — Interface Segregation Principle

Keep contracts narrow.

Examples:

- Request persistence should not expose Zendesk credential methods;
- webhook processing should not need configuration-provisioning methods;
- frontend Views should only receive the API functions they need.

Avoid one giant interface/service containing every operation in the application.

## D — Dependency Inversion Principle

Higher-level workflow should depend on clear service/repository/integration boundaries rather than embedding infrastructure everywhere.

Current implementation already separates Controllers, Services and database access, although it still imports concrete Python functions rather than using a full interface container.

For this interview scope that is acceptable. A production system could introduce Protocols/interfaces and dependency injection where testing or multiple implementations justify them.

---

# 19. Commenting and Documentation Standard

Comments should explain **why**, not narrate obvious code.

Good comment:

```text
Re-read Zendesk immediately before mutation so the system cannot deploy a
configuration different from the plan the administrator approved.
```

Bad comment:

```text
Set current fingerprint.
```

Rules:

1. use short docstrings for public service functions when purpose or side effects are not obvious;
2. comment security boundaries, transaction decisions, failure-isolation behavior and unusual Zendesk API constraints;
3. explain idempotency and retry assumptions where relevant;
4. do not comment simple assignments, loops or framework boilerplate;
5. never place secrets, credentials or real tokens in comments;
6. keep comments synchronized with behavior;
7. prefer descriptive names over compensating for unclear code with paragraphs of comments.

---

# 20. Naming Convention

Physical code follows language conventions:

```text
Python files/functions    snake_case
Python classes            PascalCase
React components          PascalCase
JavaScript functions      camelCase
Environment variables     UPPER_SNAKE_CASE
API paths                  lower-case REST paths
```

Documentation may use conceptual names such as:

```text
RequestController
RequestService
RequestRepository
AssetRequest Model
DbContext
RequestView
Partial View
Shared View
```

These conceptual names exist to make the architecture easy to explain even where the actual filename follows Python/React conventions.

---

# 21. End-to-End Request Mapping

This section maps the most important application flows file by file.

## Flow A — Create a new asset request

```text
Employee
  ↓
RequestView.jsx                         VIEW
  ↓
AssetRequestForm.jsx                    PARTIAL VIEW
  ↓
frontend/src/services/api.js            FRONTEND SERVICE
  ↓
POST /api/requests
  ↓
request_controller.py                   CONTROLLER
  ↓
schemas/request_schema.py               DTO / VALIDATION
  ↓
request_service.py                      SERVICE
  ↓
repositories/request_repository.py      REPOSITORY
  ↓
asset_request.py + audit_log.py         MODELS
  ↓
data/db_context.py + data/session.py     DB CONTEXT
  ↓
PostgreSQL                              DATABASE
  ↓
COMMIT LOCAL REQUEST FIRST
  ↓
zendesk_service.py                      EXTERNAL-INTEGRATION SERVICE
  ↓
Zendesk Tickets API                     EXTERNAL SYSTEM
  ↓
update local Zendesk ID/sync state
  ↓
Controller response
  ↓
RequestView / RequestDetailView         VIEW
```

The critical reliability decision is that PostgreSQL is committed before Zendesk ticket creation.

## Flow B — Track an existing request

```text
Employee searches or filters the Dashboard
  ↓
DashboardView.jsx                       VIEW
  ↓
Employee opens a request
  ↓
RequestDetailView.jsx                   VIEW
  ↓
frontend API service
  ↓
GET /api/requests/{id}
  ↓
request_controller.py                   CONTROLLER
  ↓
request_service.py                      SERVICE
  ↓
repositories/request_repository.py      REPOSITORY
  ↓
AssetRequest Model
  ↓
data/db_context.py / session.py          DB CONTEXT
  ↓
PostgreSQL
  ↓
response
  ↓
RequestDetailView.jsx                   VIEW
```

## Flow C — Configure Zendesk

```text
Admin
  ↓
ZendeskSetupView.jsx                    VIEW
  ↓
frontend API service
  ↓
POST /api/zendesk/connect
  ↓
zendesk_controller.py                   CONTROLLER
  ↓
zendesk_service.py                      SERVICE
  ↓
Zendesk API                             EXTERNAL SYSTEM
  ↓
read Brand / Group / Fields / Form / View / Targets / Webhooks / Triggers
  ↓
return CREATE / REUSE plan
  ↓
ZendeskSetupView.jsx                    VIEW
  ↓
Human approves fingerprint
  ↓
POST /api/zendesk/apply
  ↓
zendesk_controller.py                   CONTROLLER
  ↓
zendesk_service.py                      SERVICE
  ↓
create/reuse + verify Zendesk resources
  ↓
ZendeskConnection Model
  ↓
data/db_context.py + PostgreSQL      DB CONTEXT / DATABASE
```

## Flow D — Zendesk status change updates Track a Request

```text
Zendesk agent changes ticket status
  ↓
Zendesk Trigger
  ↓
Zendesk Webhook
  ↓
POST /api/webhooks/zendesk
  ↓
webhook_controller.py                   CONTROLLER
  ↓
webhook_service.py                      SERVICE
  ↓
repositories/request_repository.py      REPOSITORY
  ↓
AssetRequest + AuditLog                  MODELS
  ↓
PostgreSQL                               DATABASE
  ↓
RequestDetailView polling
  ↓
GET /api/requests/{id}
  ↓
updated status appears in VIEW
```

---

# 22. Hosted Architecture

```text
┌────────────────────────────────────┐
│ VIEW LAYER                         │
│ React + Vite on Render Static Sites │
│                                    │
│ RequestView                        │
│ DashboardView                      │
│ RequestDetailView                  │
│ SettingsView / ZendeskSetupView    │
│ Shared / Partial components        │
└──────────────────┬─────────────────┘
                   │ HTTPS / JSON / Basic Auth
                   ▼
┌────────────────────────────────────┐
│ CONTROLLER / SERVICE LAYERS        │
│ FastAPI on Render                  │
│                                    │
│ RequestController                  │
│ ZendeskController                  │
│ WebhookController                  │
│        ↓                           │
│ RequestService                     │
│ ZendeskService                     │
│ WebhookService                     │
└──────────────┬──────────────┬──────┘
               │              │
               ▼              ▼
┌─────────────────────┐   ┌──────────────────────────┐
│ DATA / MODEL LAYER  │   │ EXTERNAL INTEGRATION     │
│ Render PostgreSQL   │   │ Zendesk Sandbox          │
│                     │   │                          │
│ Repository          │   │ Brand / Group            │
│ DbContext/Session   │   │ Ticket Fields / Form     │
│ AssetRequest Model  │   │ View                     │
│ AuditLog Model      │   │ Email Target             │
│ ZendeskConnection   │   │ Webhook                  │
└─────────────────────┘   │ Triggers                 │
                          │ Tickets                  │
                          └────────────┬─────────────┘
                                       │ status changed
                                       ▼
                          WebhookController / Service
                                       │
                                       ▼
                              update PostgreSQL
                                       │
                                       ▼
                              Track a Request View
```

Local development may use SQLite through the same SQLAlchemy models.

---

# 23. Security

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

# 24. Environment Variables

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

Frontend / Render Static Site:

```env
VITE_API_URL=https://royal-tires-api.onrender.com
```

No server secret belongs in a Vite environment variable.

---

# 25. Database Tables

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

## `zendesk_connection`

Stores verified safe metadata and core Zendesk IDs used for ticket creation.

Workflow resources such as targets, webhooks and triggers are rediscovered by exact managed names rather than requiring extra database columns.

---

# 26. Application Pages

## `/request`

Fields:

- requester name;
- requester email;
- asset type;
- business reason.

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

## `/dashboard`

Search and filter requests by request ID, requester, email, asset, Zendesk ticket and sync state. Open any row to inspect the full request.

## `/requests/:id`

Display request details, local status, Zendesk status, sync state and timestamps. The page includes **Refresh status** and silently reads the local API every 10 seconds while open.

## `/settings`

Authenticated settings View for account/session information, developer diagnostics and the governed Zendesk configuration workflow. `ZendeskSetupView.jsx` is rendered inside Settings.

`/requests` remains a Dashboard alias and `/zendesk-setup` remains a Settings alias so older demo links do not break.

---

# 27. Governed Zendesk Setup

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

# 28. Zendesk Discovery

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

# 29. Managed Zendesk Resources

## Core ticket configuration

```text
Brand
Royal Tyres

Group
Royal Tyres | IT Service Desk

Ticket Field
RT | Asset Type
API type: tagger
Options: rt_asset_laptop, rt_asset_monitor, rt_asset_mouse, rt_asset_keyboard,
         rt_asset_headset, rt_asset_docking_station, rt_asset_other

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

Asset option tags use the `rt_asset_` prefix because Zendesk requires tags to be unique across ticket fields. The sandbox's unrelated Query Types field already uses `other`. UI labels and local asset values remain Laptop, Monitor, etc.; the Zendesk service maps those labels to the namespaced field values.

## Demo notification target

```text
Email Target
Royal Tyres | Demo Notifications

Receiver
farhaanhotd1@gmail.com
```

The receiver is configurable through `ZENDESK_NOTIFICATION_EMAIL`.

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

## Triggers

```text
Royal Tyres | Notify Demo Receiver - New Request
Royal Tyres | Notify Demo Receiver - Status Update
Royal Tyres | Sync Status to Asset Portal
```

The first two send notification emails. The third sends the status callback to FastAPI.

## Opt-in legacy safeguards

The governed plan can additionally include seven exact legacy titles: `Issue Category 1`, `Request Type 4`, `Query Type 6`, `Issue Type 6`, `Request Type 6`, `Query Type 5`, and `hello world`. The last live title has no question mark; its correction was explicitly approved after discovery.

The only permitted update adds an ALL condition, Brand IS NOT the discovered Royal Tyres brand. Existing conditions, actions, title, active state and ordering are preserved and checked on read-back. Protected rules are reused; absent exact titles are skipped. Similar titles do not authorize broader changes.

---

# 30. Dry-Run Plan

Before any mutation, the configuration View should show:

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

No mutation occurs during planning.

---

# 31. Apply Rules and Dependency Order

The administrator must approve the exact plan fingerprint.

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

Every ensure operation re-reads Zendesk and reuses an exact existing object before attempting creation.

---

# 32. Request Creation and Failure Isolation

```text
User submits request
        ↓
React View validation
        ↓
RequestController
        ↓
Pydantic Schema validation
        ↓
RequestService
        ↓
Repository / Models / DbContext
        ↓
COMMIT PostgreSQL
        ↓
ZendeskService creates ticket
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

# 33. Zendesk → Portal Status Sync

FastAPI exposes:

```text
POST /api/webhooks/zendesk
```

The endpoint uses its own bearer secret rather than portal Basic Auth.

Expected flow:

```text
Zendesk status change
    ↓
Trigger
    ↓
Webhook
    ↓
WebhookController
    ↓
WebhookService
    ↓
Repository
    ↓
AssetRequest + AuditLog Models
    ↓
DbContext / PostgreSQL
    ↓
Track a Request View polls local API
```

The browser never receives Zendesk credentials.

---

# 34. API Endpoints

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
```

Swagger/OpenAPI remains available at `/docs`.

---

# 35. Testing Map

Tests are organized by the layer/behavior they protect.

Backend examples:

```text
test_health.py      → application startup / health
test_auth.py        → Core security / Controller protection
test_security.py    → validation, CORS, security behavior
test_requests.py    → Controller + Service + Repository + Model flow
test_zendesk.py     → Zendesk Service / setup orchestration
test_webhook.py     → Webhook Controller + Service + persistence
```

Frontend examples:

```text
*.test.js           → frontend services / validation
e2e/*.spec.js       → complete View + API interaction in the browser
```

CI should continue running backend tests, frontend unit tests, Vite build and Playwright browser tests before merge.

---

# 36. Git / Pull Request History

Actual progression:

```text
PR1  chore/project-scaffold                         ✓ merged
PR2  feat/core-request-api                          ✓ merged
PR3  feat/auth-security                             ✓ merged
PR4  feat/request-ui                                ✓ merged
PR5  feat/zendesk-integration                       ✓ merged
PR6  fix/zendesk-field-types                        ✓ merged
PR7  feat/zendesk-workflow-sync                     ✓ merged
PR8  docs/mvc-architecture-map                      merged documentation baseline
```

PR8 was documentation-only. PR9–PR17 subsequently added integration fixes, safeguards, validation, dashboard/presentation and the physical MVC structure. README records that progression; section 4 describes the current physical layout.

---

# 37. Physical Structure Status

The physical MVC structure is implemented. Section 4 is the current folder map; no further folder reorganization is required for the interview. Services own transaction sequencing, repositories receive scoped Sessions, and identity helpers are shared by outbound tickets and inbound callbacks.

---

# 38. Live Demo Sequence

```text
1. Log into Royal Tyres portal.
2. Explain View → Controller → Service → Repository → Model → DbContext.
3. Open Zendesk Setup View.
4. Test environment connection.
5. Show live CREATE / REUSE plan.
6. Point out Brand, Group, Fields, Form, View, Email Target, Webhook and Triggers.
7. Approve the exact fingerprinted plan.
8. Apply and show PASS verification.
9. Submit a new Laptop request from RequestView.
10. Explain RequestController → RequestService → Repository → AssetRequest Model → PostgreSQL.
11. Show local request ID and real Zendesk ticket ID.
12. Show notification email arriving.
13. Open the Zendesk ticket.
14. Change ticket status, for example New → Pending.
15. Show status-update email arriving.
16. Return to RequestDetailView.
17. Show local status = Pending and updated sync timestamp.
18. Explain Zendesk Trigger → WebhookController → WebhookService → Model/DB → View.
```

---

# 39. Interview Architecture Explanation

A concise explanation:

> I mapped the application around MVC even though the frontend and backend use different frameworks. React contains the Views and reusable Partial/Shared View equivalents. FastAPI routers are the Controllers. Controllers stay thin and call Services for business workflow. Services use a Repository/data layer against SQLAlchemy Models, and `data/` acts as the DbContext equivalent by owning the engine and scoped sessions. Schemas are the DTO/ViewModel boundary. Middleware handles cross-cutting HTTP behavior. Zendesk is treated as an external integration Service. That gives me one consistent path to reason about the system: View → Controller → Service → Repository → Model → DbContext → Database.

For Zendesk specifically:

> PostgreSQL is the primary system of record, so the request is committed before the Zendesk call. Zendesk credentials stay only in Render. The setup View asks the Zendesk Controller to test and discover the instance. The Zendesk Service creates a fingerprinted CREATE/REUSE plan, and nothing is mutated until the administrator explicitly approves it. Status changes return through the Zendesk webhook into the Webhook Controller/Service and update the same AssetRequest Model, which the Track a Request View then reads.

---

# 40. Implementation Rules

1. Treat this file as the source of truth.
2. Use MVC as the primary mental map.
3. Views display and collect data; they do not own backend business rules.
4. Controllers handle HTTP and stay thin.
5. Services own business workflow and sequencing.
6. Repositories own database access.
7. Models represent persisted state.
8. `data/` is the current DbContext-equivalent infrastructure.
9. Schemas are the API DTO/ViewModel boundary.
10. Middleware owns cross-cutting HTTP behavior.
11. Helpers must remain small and reusable; business use cases belong in Services.
12. Core owns application-wide configuration, security and logging.
13. Shared/Partial View equivalents should be reusable React components/layouts.
14. Follow SOLID where it improves clarity; do not manufacture abstractions solely to claim compliance.
15. Comment why, not what.
16. Never expose or commit secrets.
17. Never use `dangerouslySetInnerHTML`.
18. Use SQLAlchemy/parameterized queries rather than interpolated SQL.
19. Commit the local request before any Zendesk ticket call.
20. Zendesk failure must not lose the request.
21. Discovery/dry run must remain read-only.
22. External configuration requires explicit approved-plan fingerprint.
23. Re-read Zendesk before mutation and reject stale plans.
24. Never delete unrelated Zendesk configuration.
25. Keep Swagger available.
26. Keep `/health` public.
27. Run CI before merging behavior-changing PRs.
28. Prefer code that can be explained under questioning over clever architecture for its own sake.

---

# 41. Definition of Done

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

Architecture mapping:

- [x] Models identified
- [x] Views identified
- [x] Controllers identified
- [x] Services identified
- [x] Repository layer identified
- [x] DbContext equivalent identified
- [x] Schemas/DTO/ViewModel role defined
- [x] Shared View / Partial View equivalents defined
- [x] Middleware responsibility defined
- [x] Helper responsibility defined
- [x] Core responsibility defined
- [x] SOLID mapped to concrete project responsibilities
- [x] commenting convention defined
- [x] end-to-end flows mapped file by file

Core Zendesk integration:

- [x] server-side Zendesk credentials
- [x] environment connection test
- [x] live config discovery
- [x] CREATE/REUSE dry run
- [x] SHA-256 reviewed-plan fingerprint
- [x] explicit approval gate
- [x] stale-plan rejection
- [x] Brand/Group/Fields/Form/View provisioning logic
- [x] Email Target/Webhook/Trigger provisioning logic
- [x] ticket-creation logic
- [x] local persistence before Zendesk
- [x] inbound webhook endpoint
- [x] local status/audit update logic
- [x] tracking-page polling
- [x] PR7 CI green

Live verification still required:

- [ ] refreshed live dry-run reviewed
- [ ] full Zendesk apply verified
- [ ] new-request email live-tested
- [ ] Zendesk status → portal sync live-tested

Later if time remains:

- [ ] manual Zendesk reconciliation endpoint
- [x] operations dashboard
- [x] physical MVC architecture structure
- [ ] final presentation/demo hardening

---

# 42. Final Principle

```text
VIEW
  ↓
CONTROLLER
  ↓
SERVICE
  ↓
REPOSITORY
  ↓
MODEL
  ↓
DB CONTEXT
  ↓
DATABASE
```

Around that flow:

```text
Shared/Partial Views → reusable UI
Schemas              → validated contracts
Middleware           → cross-cutting HTTP behavior
Helpers              → small reusable utilities
Core                 → configuration/security/logging
Zendesk              → external integration through Services
```

The goal is not the largest system. The goal is a **small, understandable and demonstrably reliable application whose architecture can be explained file by file under questioning**.

The owner subsequently approved six additional exact safeguards after ticket 55 proved interference: `Issue Category 2 2` (27601293620508), `Request Type 5` (27625845148444), `Query Type 7` (27650068343452), `Issue Type 7` (27695967421724), `Request Type 7` (27698487674012), and `Query Type 6 (2)` (28370722368028). The opt-in allowlist now contains thirty confirmed titles. Each receives only Brand IS NOT Royal Tyres; unrelated automation remains untouched. Discovery-to-write drift is rejected with HTTP 409.

Following ticket 56 audit evidence, the owner also approved `Query Type 8` (27650061836572), `Issue Type 8` (27695960731292), `Request Type 8` (27698470929052), and `Query Type 7 (2)` (28370770616604), under the same preservation and drift rules.

The owner approved the remaining thirteen exact active tag-replacement rules after reviewing the complete inventory: `Query Type 9` (27650056621980), `Query Type 10` (27650047286556), `Issue Type 9` (27695960756636), `Issue Type 10` (27695935951644), `Request Type 9` (27698464442908), `Request Type 10` (27698464469660), `Request Type 11` (27698464480668), `Request Type 6 (2)` (27698493243036), `Request Type 7 (2)` (27698468769436), `Request Type 8 (2)` (27698482470044), `Request Type 9 (2)` (27698501217564), `Request Type 10 (2)` (27698476163868), `Request Type 11 (2)` (27698504442140). This completes the thirty-title explicit allowlist; it does not authorize arbitrary future rules.

Webhook input accepts case-normalized Zendesk display labels (for example `Pending`) while persistence and responses remain canonical lowercase. Unsupported statuses still fail schema validation.
