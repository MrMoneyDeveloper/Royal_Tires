from pathlib import Path
import re
import subprocess


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Expected text not found while updating {label}: {old!r}")
    return text.replace(old, new, 1)


# Remove the final dependency on the retired root database module.
zendesk = Path("backend/app/services/zendesk_service.py")
text = zendesk.read_text()
text = replace_once(
    text,
    "from app.database import utc_now",
    "from app.data.base import utc_now",
    "zendesk_service.py",
)
zendesk.write_text(text)

# Restore the stable UI wording from main so PR17 remains a structure-only refactor,
# then point validation at its new Helpers location.
form = Path("frontend/src/components/AssetRequestForm.jsx")
main_form = subprocess.check_output(
    ["git", "show", "origin/main:frontend/src/components/AssetRequestForm.jsx"],
    text=True,
)
main_form = main_form.replace(
    "../services/validation.js",
    "../helpers/validation.js",
    1,
)
form.write_text(main_form)

# Remove the compatibility module itself.
Path("backend/app/database.py").unlink(missing_ok=True)

readme = Path("README.md")
text = readme.read_text()
text = text.replace(
    "`backend/app/database.py` remains only as a small compatibility facade for older imports in the large Zendesk integration module. Engine/session/base implementation lives in `data/`; new code imports from the physical data layer.\n",
    "SQLAlchemy infrastructure lives exclusively in `backend/app/data/`. Controllers and services import the data/session modules directly; there is no root database compatibility facade.\n",
)
readme.write_text(text)

spec = Path("PROJECT_SPEC.md")
text = spec.read_text()

new_map = r'''# 4. Current Physical Repository Map

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

# 5. Model Layer'''

text, count = re.subn(
    r"# 4\. Current Physical Repository Map.*?---\n\n# 5\. Model Layer",
    new_map,
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not replace PROJECT_SPEC physical repository map.")

replacements = {
    "| Repository | SQLAlchemy data access functions |":
        "| Repository | SQLAlchemy data access in `backend/app/repositories/` |",
    "| DbContext | `database.py`, SQLAlchemy engine, Base and scoped Session |":
        "| DbContext | `backend/app/data/` (`base.py`, `db_context.py`, `session.py`) |",
    "| ViewModel / DTO | Pydantic schemas in `backend/app/schemas.py` |":
        "| ViewModel / DTO | Pydantic schemas in `backend/app/schemas/` |",
    "Current physical location:\n\n```text\nbackend/app/repository.py\n```":
        "Current physical location:\n\n```text\nbackend/app/repositories/\n```",
    "Current physical location:\n\n```text\nbackend/app/schemas.py\n```":
        "Current physical location:\n\n```text\nbackend/app/schemas/\n```",
    "For the MVC mental model, the following current code is the **DbContext equivalent**:\n\n```text\nbackend/app/database.py\n```":
        "For the MVC mental model, the SQLAlchemy **DbContext equivalent** is physically split by responsibility:\n\n```text\nbackend/app/data/base.py\nbackend/app/data/db_context.py\nbackend/app/data/session.py\n```",
    "Current middleware behavior is partly defined directly in:\n\n```text\nbackend/app/main.py\n```":
        "Current middleware is physically isolated in:\n\n```text\nbackend/app/middleware/request_logging.py\nbackend/app/middleware/security_headers.py\n```",
    "There is not currently a dedicated `helpers/` folder. Some helper-like logic currently lives close to the Services/Core code that uses it.":
        "Dedicated helper folders now contain small reusable pure utilities without owning business workflow.",
    "`App.jsx` currently owns routing/session/application-shell behavior. Shared layout responsibilities can later be extracted into layout/shared components without changing application behavior.":
        "`App.jsx` owns routing/session composition. `AppLayout.jsx` and `AuthLayout.jsx` own the shared shells, while `components/shared/` contains reusable navigation, brand and footer partials.",
    "schemas.py                              DTO / VALIDATION":
        "schemas/request_schema.py               DTO / VALIDATION",
    "repository.py                           REPOSITORY":
        "repositories/request_repository.py      REPOSITORY",
    "database.py                             DB CONTEXT":
        "data/db_context.py + data/session.py     DB CONTEXT",
    "repository/database access              REPOSITORY":
        "repositories/request_repository.py      REPOSITORY",
    "database.py / Session                   DB CONTEXT":
        "data/db_context.py / session.py          DB CONTEXT",
    "React + Vite on Vercel":
        "React + Vite on Render Static Sites",
    "Frontend / Vercel:":
        "Frontend / Render Static Site:",
}
for old, new in replacements.items():
    text = text.replace(old, new)

spec.write_text(text)
