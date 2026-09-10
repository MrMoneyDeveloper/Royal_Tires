# Interview guide

Read this alongside the [README diagrams](../README.md#interview-architecture). This is an MVC-style layered mental model, not server-rendered ASP.NET MVC. The notes describe the code, including existing exceptions, rather than an idealized architecture.

Service = why/when an operation happens. Repository = how persistence is performed. Repositories use the request-scoped Session; they do not independently open an Internet connection.

## File-by-file walkthrough

### `backend/app/main.py`

- **What it is:** Application composition root
- **Who calls it:** Uvicorn; tests via create_app
- **What it calls:** Settings, Data package, middleware and Controllers
- **Why it exists:** Wire infrastructure once rather than in each business use case.
- **Data handled:** Optional typed Settings override → FastAPI app, engine and session factory; public health/OpenAPI routes
- **Security / reliability:** Lifespan creates missing tables and disposes the engine; create_all is not a migration system. Validation responses omit raw input; unexpected errors expose only a generic response.
- **One interview sentence:** “Application composition root: wire infrastructure once rather than in each business use case.”

### `backend/app/controllers/request_controller.py`

- **What it is:** Request Controller: HTTP boundary for create/list/detail
- **Who calls it:** React api.js through /api/requests
- **What it calls:** RequestService; FastAPI schema/auth/session dependencies
- **Why it exists:** Keep HTTP routing separate from business sequencing and SQL.
- **Data handled:** Basic-authenticated request, AssetRequestCreate or bounded pagination → AssetRequestResponse JSON; create returns HTTP 201
- **Security / reliability:** FastAPI validates Pydantic input before the route function runs. All three routes require Basic Auth; no direct SQL or Zendesk calls.
- **One interview sentence:** “Request Controller: HTTP boundary for create/list/detail: keep HTTP routing separate from business sequencing and SQL.”

### `backend/app/controllers/zendesk_controller.py`

- **What it is:** Zendesk setup Controller and approval boundary
- **Who calls it:** Settings / ZendeskSetupView through api.js
- **What it calls:** ZendeskService and optional legacy_trigger_guard
- **Why it exists:** Translate integration errors and bind approval to a freshly discovered plan.
- **Data handled:** Authenticated connect/setup calls or explicit confirmation plus SHA-256 fingerprint → Safe setup plan, verification results or HTTP errors
- **Security / reliability:** Rejects changed plans with 409. Connect reads Zendesk but saves local connection metadata. Managed plan fingerprints describe identity/actions; they are not full remote-object hashes.
- **One interview sentence:** “Zendesk setup Controller and approval boundary: translate integration errors and bind approval to a freshly discovered plan.”

### `backend/app/controllers/webhook_controller.py`

- **What it is:** Webhook Controller: inbound status HTTP boundary
- **Who calls it:** Zendesk webhook POST /api/webhooks/zendesk
- **What it calls:** WebhookService, webhook schemas and get_db
- **Why it exists:** Keep authentication and HTTP error translation outside status persistence.
- **Data handled:** JSON ticket/status identity plus Authorization header → Acknowledgement or 401/404/409/503 error
- **Security / reliability:** Uses its own bearer secret with constant-time comparison, not portal Basic Auth. Never log the header.
- **One interview sentence:** “Webhook Controller: inbound status HTTP boundary: keep authentication and HTTP error translation outside status persistence.”

### `backend/app/services/request_service.py`

- **What it is:** Request Service: business sequencing and transaction ownership
- **Who calls it:** Request Controller
- **What it calls:** RequestRepository, AuditRepository, AssetRequest and ZendeskService
- **Why it exists:** Service decides why and when persistence happens; repositories decide how.
- **Data handled:** Validated request, injected Session and Settings → Committed primary request, audit history and integration state
- **Security / reliability:** Flush obtains the local ID; commit saves request plus REQUEST_CREATED before Zendesk. Expected ZendeskError leaves the request saved and records sync_failed; no automatic retry is implemented.
- **One interview sentence:** “Request Service: business sequencing and transaction ownership: service decides why and when persistence happens; repositories decide how.”

### `backend/app/services/webhook_service.py`

- **What it is:** Webhook Service: correlate and persist status callbacks
- **Who calls it:** Webhook Controller after authentication
- **What it calls:** RequestRepository, AuditRepository and request identity helper
- **Why it exists:** Own the status-update use case without HTTP routing concerns.
- **Data handled:** Validated event and injected Session → Updated AssetRequest plus audit event and changed flag
- **Security / reliability:** Lookup uses the linked Zendesk ticket ID; a supplied external ID must match. Repeated status events preserve state but refresh the timestamp and append a receipt audit; no event-ordering guarantee is implemented.
- **One interview sentence:** “Webhook Service: correlate and persist status callbacks: own the status-update use case without HTTP routing concerns.”

### `backend/app/services/zendesk_service.py`

- **What it is:** Zendesk integration Service: discovery, provisioning and ticket creation
- **Who calls it:** Zendesk Controller, RequestService and legacy trigger guard
- **What it calls:** Zendesk REST API via httpx; ZendeskRepository and request identity helpers
- **Why it exists:** Keep external HTTP payloads and dependency order out of request routes.
- **Data handled:** Server Settings, verified metadata, approved setup invocation or committed request → Safe plans/errors, read-back results, connection metadata or ticket response
- **Security / reliability:** Secrets stay server-side; errors redact known secrets. Core resources reuse matching names and verify returned IDs. Connection metadata goes through ZendeskRepository using the injected Session; the service retains transaction ownership.
- **One interview sentence:** “Zendesk integration Service: discovery, provisioning and ticket creation: keep external HTTP payloads and dependency order out of request routes.”

### `backend/app/services/legacy_trigger_guard.py`

- **What it is:** Opt-in Service for seven confirmed legacy trigger exclusions
- **Who calls it:** Zendesk Controller within governed setup
- **What it calls:** ZendeskService HTTP/discovery helpers
- **Why it exists:** Isolate known sandbox interference without disabling unrelated automation.
- **Data handled:** Settings and discovered Royal Tyres brand ID → UPDATE/REUSE/SKIP plan and preservation verification
- **Security / reliability:** Only listed titles may change. Adds Brand IS NOT Royal Tyres and resends existing actions because updating conditions alone can clear actions. Snapshots contribute to the controller plan; read-back compares protected properties.
- **One interview sentence:** “Opt-in Service for seven confirmed legacy trigger exclusions: isolate known sandbox interference without disabling unrelated automation.”

### `backend/app/repositories/request_repository.py`

- **What it is:** Request Repository: ORM persistence operations
- **Who calls it:** RequestService and WebhookService
- **What it calls:** AssetRequest and the supplied SQLAlchemy Session
- **Why it exists:** Encapsulate how add/get/list/ticket lookup are performed.
- **Data handled:** Session, entity, local/ticket ID or pagination → Added entity, matching entity or ordered list
- **Security / reliability:** Receives a Session; does not open its own Internet connection or commit. ORM values are bound parameters, not interpolated SQL.
- **One interview sentence:** “Request Repository: ORM persistence operations: encapsulate how add/get/list/ticket lookup are performed.”

### `backend/app/repositories/audit_repository.py`

- **What it is:** Audit Repository: append persisted workflow history
- **Who calls it:** RequestService and WebhookService
- **What it calls:** AuditLog and supplied Session
- **Why it exists:** Centralize construction of audit records while services choose event timing.
- **Data handled:** Request ID, event type, source and safe message → Pending AuditLog entity for the service transaction
- **Security / reliability:** No authentication/session state is stored here. Service commits the audit with its related state change.
- **One interview sentence:** “Audit Repository: append persisted workflow history: centralize construction of audit records while services choose event timing.”

### `backend/app/repositories/zendesk_repository.py`

- **What it is:** Zendesk metadata Repository: singleton add/get helpers
- **Who calls it:** ZendeskService
- **What it calls:** ZendeskConnection and supplied Session
- **Why it exists:** Express metadata persistence operations separately from external HTTP.
- **Data handled:** Session and optional connection entity → Singleton metadata record or pending added entity
- **Security / reliability:** No token persistence or independent connection creation. ZendeskService owns when metadata is saved and committed; this repository owns add/get operations.
- **One interview sentence:** “Zendesk metadata Repository: singleton add/get helpers: express metadata persistence operations separately from external HTTP.”

### `backend/app/models/asset_request.py`

- **What it is:** AssetRequest Model: asset_requests SQL table
- **Who calls it:** RequestService constructs; repositories and Data persist/query
- **What it calls:** Declarative Base and SQLAlchemy column mapping
- **Why it exists:** Define the system-of-record representation independently of API DTOs.
- **Data handled:** Requester, asset, reason and integration state → Persisted primary request entity
- **Security / reliability:** Database-generated id is the primary key. Nullable unique zendesk_ticket_id is an external identifier, not a local foreign key. Hosted storage is PostgreSQL; SQLite is for local/test use.
- **One interview sentence:** “AssetRequest Model: asset_requests SQL table: define the system-of-record representation independently of API DTOs.”

### `backend/app/models/audit_log.py`

- **What it is:** AuditLog Model: audit_logs SQL table
- **Who calls it:** AuditRepository
- **What it calls:** Declarative Base; foreign key to asset_requests.id
- **Why it exists:** One AssetRequest can have many audit events for diagnosis and explanation.
- **Data handled:** Event type/source/message/time and request_id → Persisted chronological workflow history in PostgreSQL
- **Security / reliability:** id is the audit primary key. request_id is the foreign key linking the event to AssetRequest. AuditLog is NOT authentication or browser-session state; no ORM relationship property is required to enforce the SQL foreign key.
- **One interview sentence:** “AuditLog Model: audit_logs SQL table: one AssetRequest can have many audit events for diagnosis and explanation.”

### `backend/app/models/zendesk_connection.py`

- **What it is:** ZendeskConnection Model: singleton zendesk_connection table
- **Who calls it:** ZendeskService; metadata repository helpers
- **What it calls:** Declarative Base and SQLAlchemy columns
- **Why it exists:** Reuse verified integration IDs without storing credentials in SQL.
- **Data handled:** Safe account metadata, managed IDs and verification timestamps → Persisted singleton metadata, conventionally id=1
- **Security / reliability:** id is the local primary key. Brand/group/field/form/view IDs come from Zendesk, not local foreign keys. API token remains in server configuration.
- **One interview sentence:** “ZendeskConnection Model: singleton zendesk_connection table: reuse verified integration IDs without storing credentials in SQL.”

### `backend/app/schemas/request_schema.py`

- **What it is:** Request/response Schemas: Pydantic DTO contracts
- **Who calls it:** FastAPI Request Controller
- **What it calls:** Pydantic field checks and reason validator
- **Why it exists:** Separate API validation from persisted database representation.
- **Data handled:** Untrusted request JSON; response ORM attributes → Validated AssetRequestCreate or serialized AssetRequestResponse
- **Security / reliability:** Rejects extra fields, invalid email/assets/lengths. Reason must contain 10 non-whitespace characters; valid formatting is preserved. A schema is not a database table.
- **One interview sentence:** “Request/response Schemas: Pydantic DTO contracts: separate API validation from persisted database representation.”

### `backend/app/schemas/zendesk_schema.py`

- **What it is:** Setup Schemas: approval and safe response contracts
- **Who calls it:** FastAPI Zendesk Controller
- **What it calls:** Pydantic types, patterns and action literals
- **Why it exists:** Specify the browser/backend contract without exposing integration credentials.
- **Data handled:** Confirmation/fingerprint or safe setup result → Validated apply input and bounded response structure
- **Security / reliability:** Apply forbids extra fields and requires a 64-character lowercase hex fingerprint; confirmation itself is checked by the controller. Models persist data; these schemas describe HTTP data.
- **One interview sentence:** “Setup Schemas: approval and safe response contracts: specify the browser/backend contract without exposing integration credentials.”

### `backend/app/schemas/webhook_schema.py`

- **What it is:** Webhook Schemas: event and acknowledgement contracts
- **Who calls it:** FastAPI Webhook Controller
- **What it calls:** Pydantic literals and constraints
- **Why it exists:** Validate external event shape before business processing.
- **Data handled:** Event, positive ticket ID, optional external ID and status → Typed event or validation error; acknowledgement fields
- **Security / reliability:** Rejects extra fields and unsupported statuses. External ID is optional in this contract; WebhookService checks it when supplied. Schema validation does not replace bearer authentication.
- **One interview sentence:** “Webhook Schemas: event and acknowledgement contracts: validate external event shape before business processing.”

### `backend/app/data/base.py`

- **What it is:** Data foundation: declarative Base and UTC timestamp type
- **Who calls it:** SQLAlchemy Models; services use utc_now
- **What it calls:** SQLAlchemy declarative mapping and datetime
- **Why it exists:** Share mapping infrastructure across models.
- **Data handled:** Model definitions and database timestamp results → Shared metadata registry and UTC-aware values
- **Security / reliability:** UTCDateTime restores UTC metadata when SQLite returns naive values. Base collects tables; it neither authenticates users nor owns business workflow.
- **One interview sentence:** “Data foundation: declarative Base and UTC timestamp type: share mapping infrastructure across models.”

### `backend/app/data/db_context.py`

- **What it is:** Data infrastructure: SQLAlchemy engine construction
- **Who calls it:** main.create_app
- **What it calls:** SQLAlchemy create_engine and SQLite connection event
- **Why it exists:** Keep driver/connection policy in one place.
- **Data handled:** DATABASE_URL supplied through Settings → Engine with driver configuration and connection pool
- **Security / reliability:** Normalizes PostgreSQL URLs to psycopg and enables local SQLite foreign keys. pool_pre_ping checks reused connections. Data package approximates ApplicationDbContext infrastructure; no literal Entity Framework DbContext exists.
- **One interview sentence:** “Data infrastructure: SQLAlchemy engine construction: keep driver/connection policy in one place.”

### `backend/app/data/session.py`

- **What it is:** Data infrastructure: session factory and scoped dependency
- **Who calls it:** main.create_app and Controllers through Depends(get_db)
- **What it calls:** SQLAlchemy sessionmaker bound to the shared Engine
- **Why it exists:** Give repositories/services one shared unit of work per request.
- **Data handled:** Engine or FastAPI Request carrying app state → One Session yielded per HTTP request, closed afterward
- **Security / reliability:** Services explicitly commit; closing the Session releases connections and rolls back uncommitted work. Repositories receive/use this Session rather than independently creating network connections.
- **One interview sentence:** “Data infrastructure: session factory and scoped dependency: give repositories/services one shared unit of work per request.”

### `backend/app/middleware/request_logging.py`

- **What it is:** HTTP middleware: safe response-path request logging
- **Who calls it:** main registers it; FastAPI invokes it around requests
- **What it calls:** call_next then app.http logger
- **Why it exists:** Observe endpoint outcomes without copying request bodies or credentials.
- **Data handled:** HTTP method, matched route template and returned status → Unchanged response plus safe log entry
- **Security / reliability:** Request enters, continues toward Controller, and returning response is logged. Current implementation records method/route/status only, not elapsed timing, query strings or Authorization headers.
- **One interview sentence:** “HTTP middleware: safe response-path request logging: observe endpoint outcomes without copying request bodies or credentials.”

### `backend/app/middleware/security_headers.py`

- **What it is:** HTTP middleware: response MIME/cache controls
- **Who calls it:** main registers it; FastAPI invokes it around requests
- **What it calls:** call_next and response headers
- **Why it exists:** Apply the same response policy to all API routes.
- **Data handled:** Request path and downstream response → nosniff header; no-store on /api/ responses
- **Security / reliability:** X-Content-Type-Options: nosniff tells browsers not to infer another MIME type. Cache-Control: no-store asks caches not to store API responses. Neither is cookie protection or the reason an API is stateless.
- **One interview sentence:** “HTTP middleware: response MIME/cache controls: apply the same response policy to all API routes.”

### `backend/app/helpers/request_identity.py`

- **What it is:** Pure integration identity helpers
- **Who calls it:** WebhookService and ZendeskService
- **What it calls:** String formatting only
- **Why it exists:** Make deterministic identity rules understandable outside workflow code.
- **Data handled:** Local request ID or asset label → Correlation external ID, request tag or namespaced asset value
- **Security / reliability:** royal-tires-asset-{local_request_id} is correlation, not encryption, hashing or the database primary key. Outbound ticket creation and inbound correlation share the same deterministic identity rules.
- **One interview sentence:** “Pure integration identity helpers: make deterministic identity rules understandable outside workflow code.”

### `backend/app/core/config.py`

- **What it is:** Core configuration: environment to typed Settings
- **Who calls it:** main.create_app; tests may inject Settings
- **What it calls:** Pydantic BaseSettings and origin validator
- **Why it exists:** Runtime injection means the host supplies values when the app runs instead of hard-coding them into GitHub.
- **Data handled:** DATABASE_URL, APP_USERNAME, APP_PASSWORD, FRONTEND_URL; ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN, ZENDESK_WEBHOOK_SECRET, ZENDESK_NOTIFICATION_EMAIL, RENDER_EXTERNAL_URL → Typed settings consumed by Data, authentication, CORS and Zendesk
- **Security / reliability:** Host environment overrides local .env defaults. SecretStr masks normal secret display, but values must still never be logged; DATABASE_URL is also sensitive. Explicit CORS origins are validated. The legacy safeguard is opt-in.
- **One interview sentence:** “Core configuration: environment to typed Settings: runtime injection means the host supplies values when the app runs instead of hard-coding them into GitHub.”

### `backend/app/core/security.py`

- **What it is:** Core authentication: assignment-required HTTP Basic
- **Who calls it:** Request and Zendesk router dependencies
- **What it calls:** Settings and constant-time credential comparisons
- **Why it exists:** Share endpoint authentication without mixing it into business services.
- **Data handled:** Basic credentials from the HTTP request → Authenticated username or 401/503
- **Security / reliability:** Base64 is encoding, not encryption; hosted HTTPS protects transport. Empty server credentials fail closed. No server-side login session or AuditLog-based authentication exists.
- **One interview sentence:** “Core authentication: assignment-required HTTP Basic: share endpoint authentication without mixing it into business services.”

### `backend/app/core/logging_config.py`

- **What it is:** Core logging policy
- **Who calls it:** main lifespan
- **What it calls:** Python logging configuration
- **Why it exists:** Choose log format and levels once at startup.
- **Data handled:** Logger configuration, not user credentials → INFO application logs; quieter httpx logs
- **Security / reliability:** Suppresses routine httpx URLs at INFO. This is not a universal redactor: callers must keep secrets out; ZendeskService separately sanitizes upstream errors.
- **One interview sentence:** “Core logging policy: choose log format and levels once at startup.”

### `frontend/src/main.jsx`

- **What it is:** React entry point
- **Who calls it:** Vite-built browser entry
- **What it calls:** ReactDOM, App and shared CSS
- **Why it exists:** Keep browser bootstrapping separate from routes and pages.
- **Data handled:** Root DOM element → Mounted React application
- **Security / reliability:** StrictMode may repeat development effects; no credentials are embedded here.
- **One interview sentence:** “React entry point: keep browser bootstrapping separate from routes and pages.”

### `frontend/src/App.jsx`

- **What it is:** Client composition: routes and in-memory login state
- **Who calls it:** main.jsx
- **What it calls:** api.js, page Views, AppLayout and AuthLayout
- **Why it exists:** Keep route/session composition outside page presentation.
- **Data handled:** Browser pathname and login form data → Selected page and authenticated API client passed as props
- **Security / reliability:** Login probes listRequests; credentials live in the API closure, not localStorage. Refresh/sign-out drops that reference. Optional GSAP respects reduced-motion preferences.
- **One interview sentence:** “Client composition: routes and in-memory login state: keep route/session composition outside page presentation.”

### `frontend/src/services/api.js`

- **What it is:** Frontend HTTP Service
- **Who calls it:** App login and page Views
- **What it calls:** fetch to the configured FastAPI origin
- **Why it exists:** Centralize auth headers, timeout and HTTP error handling.
- **Data handled:** In-memory portal credentials and request DTOs → JSON response or ApiError
- **Security / reliability:** Never calls Zendesk. Basic Auth is sent over hosted HTTPS; no credential persistence. Default request timeout is 30 seconds, including setup operations; a timeout alone does not prove the server stopped.
- **One interview sentence:** “Frontend HTTP Service: centralize auth headers, timeout and HTTP error handling.”

### `frontend/src/views/RequestView.jsx`

- **What it is:** Page View: create request and show result
- **Who calls it:** App for /request
- **What it calls:** AssetRequestForm, api.createRequest, AppLink and StatusBadge
- **Why it exists:** Own page-level submission state without SQL or Zendesk HTTP logic.
- **Data handled:** Form values and injected api/navigate → Created request summary or error
- **Security / reliability:** Renders response text normally. The backend, not this page, guarantees commit-before-Zendesk.
- **One interview sentence:** “Page View: create request and show result: own page-level submission state without SQL or Zendesk HTTP logic.”

### `frontend/src/views/RequestDetailView.jsx`

- **What it is:** Page View: track one persisted request
- **Who calls it:** App for /requests/:id
- **What it calls:** api.getRequest, formatting helper and SyncStatePanel
- **Why it exists:** Present tracking while the backend owns synchronization.
- **Data handled:** Route ID and request DTO → Request details and latest locally stored status
- **Security / reliability:** Polls only FastAPI every 10 seconds; cleanup cancels the timer. Manual refresh is a local read, not Zendesk reconciliation. User text stays React text.
- **One interview sentence:** “Page View: track one persisted request: present tracking while the backend owns synchronization.”

### `frontend/src/views/DashboardView.jsx`

- **What it is:** Page View: searchable request dashboard
- **Who calls it:** App for /dashboard and /requests alias
- **What it calls:** api.listRequests, AppLink, StatusBadge and formatting helper
- **Why it exists:** Keep page display/search separate from backend persistence.
- **Data handled:** Up to 100 latest request DTOs; local search/filter state → Summary counts and filtered table
- **Security / reliability:** Counts/search cover the loaded 100 records, not necessarily the entire database. Loads on entry and manual refresh; no automatic dashboard polling. User data is rendered as text.
- **One interview sentence:** “Page View: searchable request dashboard: keep page display/search separate from backend persistence.”

### `frontend/src/views/SettingsView.jsx`

- **What it is:** Page View: account, diagnostics and setup composition
- **Who calls it:** App for /settings and /zendesk-setup alias
- **What it calls:** ZendeskSetupView and backend diagnostic links
- **Why it exists:** Separate administration presentation from request submission.
- **Data handled:** Username, API client and docs URL → Account summary and embedded setup View
- **Security / reliability:** Displays account context, never passwords or Zendesk credentials. Does not manage Zendesk user permissions.
- **One interview sentence:** “Page View: account, diagnostics and setup composition: separate administration presentation from request submission.”

### `frontend/src/views/ZendeskSetupView.jsx`

- **What it is:** Integration View: governed discovery and approval UI
- **Who calls it:** SettingsView
- **What it calls:** api.getZendeskSetup/connectZendesk/applyZendeskSetup; local PlanRows
- **Why it exists:** Make intended external changes reviewable before submission.
- **Data handled:** Safe setup DTO, confirmation checkbox and plan fingerprint → CREATE/REUSE/UPDATE/SKIP rows and verification results
- **Security / reliability:** Changing/reloading the plan resets approval; 409 invalidates it. Backend enforces the gate. Managed read-back PASS currently checks object IDs, not every remote property; safeguard verification is stricter.
- **One interview sentence:** “Integration View: governed discovery and approval UI: make intended external changes reviewable before submission.”

### `frontend/src/layouts/AppLayout.jsx`

- **What it is:** Layout: reusable authenticated page shell
- **Who calls it:** App
- **What it calls:** Sidebar, Topbar, Footer and children
- **Why it exists:** Share layout without duplicating page business state.
- **Data handled:** Navigation/session display props and selected page → Consistent authenticated shell
- **Security / reliability:** Receives a username and callbacks, not stored server secrets.
- **One interview sentence:** “Layout: reusable authenticated page shell: share layout without duplicating page business state.”

### `frontend/src/layouts/AuthLayout.jsx`

- **What it is:** Layout: reusable sign-in shell
- **Who calls it:** App
- **What it calls:** Brand and children
- **Why it exists:** Keep visual shell separate from login behavior.
- **Data handled:** Login form child → Unauthenticated page presentation
- **Security / reliability:** App/api.js perform sign-in; layout does not authenticate or retain credentials.
- **One interview sentence:** “Layout: reusable sign-in shell: keep visual shell separate from login behavior.”

### `frontend/src/components/AssetRequestForm.jsx`

- **What it is:** Reusable component / Partial View: request form
- **Who calls it:** RequestView
- **What it calls:** validation helper and onSubmit callback
- **Why it exists:** Reuse form validation and accessibility without owning HTTP.
- **Data handled:** User text, submission/error props → Trimmed values or inline errors
- **Security / reliability:** Client checks are usability only; backend independently validates. Whitespace does not count toward the minimum reason. Submitting state prevents repeated clicks.
- **One interview sentence:** “Reusable component / Partial View: request form: reuse form validation and accessibility without owning HTTP.”

### `frontend/src/components/AppLink.jsx`

- **What it is:** Reusable component: internal navigation link
- **Who calls it:** Views and shared navigation
- **What it calls:** Injected navigate callback or native anchor behavior
- **Why it exists:** Share navigation behavior while preserving browser conventions.
- **Data handled:** Target path, children and anchor props → SPA navigation on ordinary click
- **Security / reliability:** Modified clicks remain native links; ordinary clicks preserve the current in-memory app state.
- **One interview sentence:** “Reusable component: internal navigation link: share navigation behavior while preserving browser conventions.”

### `frontend/src/components/StatusBadge.jsx`

- **What it is:** Reusable component: readable status label
- **Who calls it:** Views and SyncStatePanel
- **What it calls:** Local statusLabel helper
- **Why it exists:** Present statuses consistently across pages.
- **Data handled:** Status string or missing value → Text badge and CSS class
- **Security / reliability:** React renders the label as text; missing status has an explicit fallback.
- **One interview sentence:** “Reusable component: readable status label: present statuses consistently across pages.”

### `frontend/src/components/SyncStatePanel.jsx`

- **What it is:** Reusable component: integration status presentation
- **Who calls it:** RequestDetailView
- **What it calls:** StatusBadge, formatting helper and onRefresh
- **Why it exists:** Share sync explanation without performing integration workflow.
- **Data handled:** Persisted request DTO and refresh state → Ticket/state/timestamp display
- **Security / reliability:** Refresh delegates to the parent local-API read. Pending/failed display is not a retry or reconciliation implementation.
- **One interview sentence:** “Reusable component: integration status presentation: share sync explanation without performing integration workflow.”

### `frontend/src/components/shared/Brand.jsx`

- **What it is:** Shared component: brand identity
- **Who calls it:** AuthLayout and Sidebar
- **What it calls:** React presentation only
- **Why it exists:** Keep the same identity across shells.
- **Data handled:** No business input → Brand markup
- **Security / reliability:** Static UI only; no authentication or external API calls.
- **One interview sentence:** “Shared component: brand identity: keep the same identity across shells.”

### `frontend/src/components/shared/Sidebar.jsx`

- **What it is:** Shared component: primary navigation
- **Who calls it:** AppLayout
- **What it calls:** Brand and AppLink
- **Why it exists:** Reuse navigation across authenticated Views.
- **Data handled:** Route flags, navigation callback and docs URL → Active navigation links
- **Security / reliability:** Swagger opens separately; no credentials are placed in its URL.
- **One interview sentence:** “Shared component: primary navigation: reuse navigation across authenticated Views.”

### `frontend/src/components/shared/Topbar.jsx`

- **What it is:** Shared component: account/navigation header
- **Who calls it:** AppLayout
- **What it calls:** AppLink and onSignOut callback
- **Why it exists:** Separate header presentation from App session ownership.
- **Data handled:** Username, breadcrumb and navigation state → Header and sign-out action
- **Security / reliability:** Displays username as text. App clears the in-memory API reference on sign-out.
- **One interview sentence:** “Shared component: account/navigation header: separate header presentation from App session ownership.”

### `frontend/src/components/shared/Footer.jsx`

- **What it is:** Shared component: footer
- **Who calls it:** AppLayout
- **What it calls:** React presentation only
- **Why it exists:** Keep shell wording in one reusable component.
- **Data handled:** No business input → Static footer markup
- **Security / reliability:** No persistence, authentication or network behavior.
- **One interview sentence:** “Shared component: footer: keep shell wording in one reusable component.”

### `frontend/src/helpers/formatting.js`

- **What it is:** Helper: timestamp display formatting
- **Who calls it:** DashboardView, RequestDetailView and SyncStatePanel
- **What it calls:** Date.toLocaleString
- **Why it exists:** Share formatting without owning page state or HTTP.
- **Data handled:** Timestamp and optional fallback → Localized date/time text
- **Security / reliability:** Output depends on browser locale/timezone; it does not change the stored UTC value.
- **One interview sentence:** “Helper: timestamp display formatting: share formatting without owning page state or HTTP.”

### `frontend/src/helpers/validation.js`

- **What it is:** Pure helper: request input checks
- **Who calls it:** AssetRequestForm and unit tests
- **What it calls:** String/regex checks only
- **Why it exists:** Keep reusable deterministic checks outside JSX.
- **Data handled:** Form values → Field error map and meaningful character count
- **Security / reliability:** No business workflow or network access. Counts non-whitespace characters; backend Pydantic remains the authoritative boundary.
- **One interview sentence:** “Pure helper: request input checks: keep reusable deterministic checks outside JSX.”

### Package and styling files

`backend/app/*/__init__.py` files declare packages or re-export symbols; `data/__init__.py` is the public Data import surface used by main. They do not introduce another runtime service. CSS files beside Views/components own presentation; global styles are imported by frontend main. `frontend/index.html` supplies the mount point and optional animation library.

### `.github/workflows/ci.yml`

- **What it is:** GitHub Actions verification workflow.
- **Who calls it:** pull requests targeting main and pushes to main.
- **What it calls:** separate Ubuntu backend and frontend jobs.
- **Why it exists:** catch regressions before merging.
- **Data handled:** checked-out source, dependency caches and test/build results.
- **One interview sentence:** “CI verifies the code; Render deployment is a separate mechanism.”

## Testing boundaries

Backend tests run FastAPI against temporary SQLite and mock Zendesk; they cover auth, input, persistence, failure isolation, setup and callbacks. Frontend unit tests use Node’s test runner. Playwright runs desktop Chrome and Pixel 7 emulation against Vite with intercepted API responses: this verifies browser behavior, not live PostgreSQL/Zendesk. The hosted verification is separate evidence. No branch-protection configuration is assumed.

## HOW TO TRACE UNKNOWN CODE DURING THE INTERVIEW

1. Read imports.
2. Identify the public route/function/class.
3. Determine who calls it.
4. Determine what it calls.
5. Identify input.
6. Identify output.
7. Follow the next architectural layer.
8. Explain why the responsibility lives here.

## Glossary

| Term | Practical meaning here |
| --- | --- |
| FastAPI | Python HTTP framework registering routes, dependency injection, validation and generated API documentation. |
| React | Renders Views/components from state; user text remains text. |
| Vite | Frontend development server and build tool; produces the static deployment bundle. |
| Pydantic | Validates API schemas and typed application settings. |
| DTO | Data Transfer Object: request/response shape crossing an API boundary. |
| Schema | Pydantic data contract; not a persisted SQL table. |
| Model | SQLAlchemy entity mapping persisted columns, such as AssetRequest. |
| SQLAlchemy | Python toolkit managing ORM mappings, queries and transactions. |
| ORM | Maps Python entities and expressions to SQL tables/operations. |
| Repository | Uses an injected Session to perform persistence operations. |
| Service | Decides business sequencing, including when to commit and call Zendesk. |
| Controller | FastAPI route boundary translating HTTP input/results into service calls. |
| Middleware | Wraps request/response processing, such as setting headers or logging the result. |
| Helper | Small reusable utility; identity/validation helpers do not own workflow. |
| DbContext mental model | Data package's Base, Engine and Session infrastructure; no literal EF DbContext. |
| Session | Request-scoped ORM unit of work tracking entities and transactions, not a browser login session. |
| Engine | SQLAlchemy driver/connection-pool infrastructure built from DATABASE_URL. |
| Dependency Injection | FastAPI Depends supplies shared auth checks and a scoped Session to routes. |
| Basic Auth | Username/password encoded into each request; HTTPS supplies transport encryption. |
| CORS | Browser policy allowing specified frontend origins; not an authentication mechanism. |
| XSS | User text becoming executable HTML/JavaScript; React text rendering prevents that path here. |
| SQL Injection | User input becoming executable SQL syntax; ORM bound parameters separate data from SQL. |
| REST | Resource-oriented HTTP API style, such as POST and GET /api/requests. |
| Stateless | Each protected request supplies auth/context; not a claim that the database stores no state. |
| Webhook | Zendesk initiates a callback to this application after a status event. |
| API | Contract for systems to communicate; outbound calls and webhooks both use APIs. |
| JSON | Structured text format used for request, response and callback bodies. |
| Foreign Key | audit_logs.request_id references asset_requests.id and enforces that link. |
| Primary Key | Database identity for a row, such as AssetRequest.id or AuditLog.id. |
| Audit Log | Persisted chronological business events, separate from operational logs and authentication. |
| CI | Automated checks on pull requests/main, independent of deployment. |
| E2E Test | Tests a user flow; repository Playwright mocks the API, so hosted E2E evidence is separate. |
| Unit Test | Isolates logic such as validation or payload generation; many backend tests also integrate FastAPI/SQLite. |
| Playwright | Automates Chromium browser tests in desktop and mobile emulation. |
| pytest | Runs backend tests with fixtures, assertions and mocked external calls. |
| Swagger | Interactive UI at /docs for the generated API definition. |
| OpenAPI | Machine-readable route/schema definition exposed at /openapi.json. |
| Environment Variable | Host-supplied configuration read by Settings; server secrets never belong in the public bundle. |
| Runtime Configuration | Values supplied when the backend runs, rather than hard-coded in source. |

## Useful boundaries to explain honestly

- Core setup read-back checks object IDs. It does not prove every property of reused resources matches the desired definition; live ticket evidence supplements it.
- The safeguard is opt-in and only recognizes its exact allowlisted titles (case-insensitive comparison). A similar title is not automatically authorized.
- The controller checks a freshly rebuilt plan fingerprint. There is no distributed lock across Zendesk discovery and mutation.
- Webhook external ID is optional in the existing schema; correlation rejects a mismatch when it is present. There is no replay-window or event-ordering mechanism.
- Database commit precedes ticket creation, but the two systems cannot share one SQL transaction. Expected integration failure is audited; reconciliation remains a later enhancement.
- Dashboard search and counts cover the latest 100 loaded records. Only RequestDetailView polls automatically.
- See [live verification](LIVE_VERIFICATION.md) for actual IDs, results and manual delivery checks. The example IDs in README are not test evidence.
