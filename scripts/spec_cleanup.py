from pathlib import Path

path = Path("PROJECT_SPEC.md")
text = path.read_text()

replacements = {
    "**Hosting:** React/Vite on Vercel, FastAPI on Render, Render PostgreSQL, Zendesk sandbox":
        "**Hosting:** React/Vite on Render Static Sites, FastAPI on Render, Render PostgreSQL, Zendesk sandbox",
    "Manual pull/reconciliation and the operations dashboard remain later enhancements. Do not add microservices, queues or infrastructure the practical does not need.":
        "Manual pull/reconciliation remains a later enhancement. The searchable operations dashboard is part of the hosted solution. Do not add microservices, queues or infrastructure the practical does not need.",
    "## Shared View / Layout equivalents currently inside `App.jsx`\n\nThe application shell currently contains shared concerns such as:\n\n```text\nBrand\nSidebar\nTopbar\nNavigation\nAccount area\nTrack-request form\nWorkspace footer\n```\n\nThese work today but are logically **Shared Views / Layouts**.\n\nFuture refactor target:\n\n```text\nfrontend/src/layouts/\n    AppLayout.jsx\n    AuthLayout.jsx\n\nfrontend/src/components/shared/\n    Brand.jsx\n    Sidebar.jsx\n    Topbar.jsx\n    Footer.jsx\n    TrackRequestForm.jsx\n```\n\nThe goal is not to create empty folders. Shared files should only be extracted when they contain a real reusable responsibility.":
        "## Shared View / Layout structure\n\nThe application shell is physically separated into real shared Views and Partial Views:\n\n```text\nfrontend/src/layouts/\n    AppLayout.jsx\n    AuthLayout.jsx\n\nfrontend/src/components/shared/\n    Brand.jsx\n    Sidebar.jsx\n    Topbar.jsx\n    Footer.jsx\n```\n\n`App.jsx` owns routing and session composition. The layout files own the authenticated and unauthenticated shells, while shared components own reusable brand/navigation/footer presentation.",
    "Future organization, if the single file becomes too large:\n\n```text\nbackend/app/repositories/\n    request_repository.py\n    audit_repository.py\n    zendesk_repository.py\n```":
        "Current repository organization:\n\n```text\nbackend/app/repositories/\n    request_repository.py\n    audit_repository.py\n    zendesk_repository.py\n```",
    "Future folder target, only if a refactor improves readability:\n\n```text\nbackend/app/data/\n    base.py\n    db_context.py\n    session.py\n```":
        "The physical data package separates declarative/timestamp concerns, engine configuration and scoped session dependencies without introducing an artificial EF-style class.",
    "Future organization if the file grows:\n\n```text\nbackend/app/schemas/\n    request_schema.py\n    zendesk_schema.py\n    webhook_schema.py\n```":
        "Current schema organization:\n\n```text\nbackend/app/schemas/\n    request_schema.py\n    zendesk_schema.py\n    webhook_schema.py\n```",
    "Future organization:\n\n```text\nbackend/app/middleware/\n    request_logging.py\n    security_headers.py\n```":
        "Current middleware organization:\n\n```text\nbackend/app/middleware/\n    request_logging.py\n    security_headers.py\n```",
    "Employee enters local request ID\n  ↓\nRequestDetailView.jsx                   VIEW":
        "Employee searches or filters the Dashboard\n  ↓\nDashboardView.jsx                       VIEW\n  ↓\nEmployee opens a request\n  ↓\nRequestDetailView.jsx                   VIEW",
    "database.py / PostgreSQL                DB CONTEXT / DATABASE":
        "data/db_context.py + PostgreSQL      DB CONTEXT / DATABASE",
    "│ React + Vite on Render Static Sites             │":
        "│ React + Vite on Render Static Sites │",
    "│ RequestView                        │\n│ RequestDetailView                  │\n│ ZendeskSetupView                   │":
        "│ RequestView                        │\n│ DashboardView                      │\n│ RequestDetailView                  │\n│ SettingsView / ZendeskSetupView    │",
    "## `/requests/:id`\n\nDisplay request details, local status, Zendesk status, sync state and timestamps.\n\nThe page includes **Refresh status** and silently reads the local API every 10 seconds while open.\n\n## `/zendesk-setup`\n\nAuthenticated administration View that tests server-side Zendesk credentials, discovers live resources, displays the governed plan, captures approval, applies configuration and shows verification results.":
        "## `/dashboard`\n\nSearch and filter requests by request ID, requester, email, asset, Zendesk ticket and sync state. Open any row to inspect the full request.\n\n## `/requests/:id`\n\nDisplay request details, local status, Zendesk status, sync state and timestamps. The page includes **Refresh status** and silently reads the local API every 10 seconds while open.\n\n## `/settings`\n\nAuthenticated settings View for account/session information, developer diagnostics and the governed Zendesk configuration workflow. `ZendeskSetupView.jsx` is rendered inside Settings.\n\n`/requests` remains a Dashboard alias and `/zendesk-setup` remains a Settings alias so older demo links do not break.",
    "POST /api/requests/{id}/sync        # later manual reconciliation\nGET  /api/dashboard/summary         # later dashboard":
        "POST /api/requests/{id}/sync        # later manual reconciliation",
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"Expected spec text not found: {old[:80]!r}")
    text = text.replace(old, new, 1)

# Add the two page-level Views introduced after the first version of the spec.
needle = "## `RequestDetailView.jsx`\n\nConceptual MVC View:"
insert = """## `DashboardView.jsx`\n\nConceptual MVC View:\n\n```text\nIT Service Desk Dashboard View\n```\n\nResponsibilities:\n\n- list and search local requests;\n- filter active, solved and sync-failed records;\n- show linked Zendesk ticket/status information;\n- navigate to one request for detailed tracking.\n\n## `SettingsView.jsx`\n\nConceptual MVC View:\n\n```text\nApplication Settings View\n```\n\nResponsibilities:\n\n- show account/session context;\n- expose API diagnostics/Swagger navigation;\n- host the governed Zendesk configuration View.\n\n## `RequestDetailView.jsx`\n\nConceptual MVC View:"""
if needle not in text:
    raise SystemExit("View-layer insertion point not found")
text = text.replace(needle, insert, 1)

path.write_text(text)
