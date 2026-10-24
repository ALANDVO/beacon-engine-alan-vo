# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

iso-analysis

## Roadmap

### project-skeleton — FastAPI/React project skeleton with health check

Status: done

Acceptance:
- FastAPI backend starts and serves /healthz
- React frontend builds and loads
- Docker compose brings up both services
- Basic pytest and vitest tests pass

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/db_utils.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/api/__init__.py`, `backend/app/api/users.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/components/ui.tsx`, `frontend/src/components/Toaster.tsx`, `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useToast.ts`, `frontend/src/api/client.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/ISOsPage.tsx`, `frontend/src/pages/RecipesPage.tsx`, `frontend/src/pages/BuildsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `backend/requirements.txt`, `frontend/package.json`, `backend/pyproject.toml`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_users.py`, `backend/tests/test_isos.py`, `backend/tests/test_recipes.py`, `backend/tests/test_builds.py`, `frontend/src/App.test.tsx`

Tests: `backend/tests/test_health.py`, `backend/tests/test_users.py`, `backend/tests/test_isos.py`, `backend/tests/test_recipes.py`, `backend/tests/test_builds.py`, `frontend/src/App.test.tsx`

### iso-analysis — ISO image analysis and metadata extraction

Status: done

Acceptance:
- Upload Windows ISO, extract version/edition/build info
- Store ISO metadata in database
- API endpoint returns parsed ISO details

Implementation: `backend/app/api/isos.py`, `backend/app/models/__init__.py (ISOImage model)`, `backend/app/schemas/__init__.py (ISOImage schemas)`, `backend/app/core/iso_parser.py`, `frontend/src/pages/ISOsPage.tsx`, `frontend/src/api/client.ts (isosApi)`

Tests: `backend/tests/test_isos.py`, `backend/tests/test_iso_parser.py`

### recipe-builder — Build recipe creation and validation

Status: done

Acceptance:
- Create/edit/clone build recipes via UI
- Recipe schema validation (components, removals, registry tweaks)
- Export recipe as JSON

Implementation: `backend/app/api/recipes.py`, `backend/app/models/__init__.py (BuildRecipe model)`, `backend/app/schemas/__init__.py (BuildRecipe schemas)`, `frontend/src/pages/RecipesPage.tsx`, `frontend/src/api/client.ts (recipesApi)`

Tests: `backend/tests/test_recipes.py`

### build-orchestration — Build job orchestration and progress tracking

Status: done

Acceptance:
- Start build job with recipe and ISO
- Track stages: mount, component cleanup, registry tweaks, unmount, ISO creation
- Real-time progress via polling
- Persist build logs and artifacts

Implementation: `backend/app/api/builds.py`, `backend/app/models/__init__.py (BuildJob, BuildLog models)`, `backend/app/schemas/__init__.py (BuildJob schemas)`, `frontend/src/pages/BuildsPage.tsx`, `frontend/src/api/client.ts (buildsApi)`

Tests: `backend/tests/test_builds.py`

### auth-oidc — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Login/logout via Keycloak
- Role-based access (viewer, operator, admin)
- Protected API endpoints
- Demo mode for local development

Implementation: `backend/app/api/users.py`, `backend/app/core/config.py (OIDC settings)`, `frontend/src/hooks/useAuth.ts`, `frontend/src/pages/SettingsPage.tsx (auth config display)`, `compose.yaml (Keycloak service)`

Tests: `backend/tests/test_users.py`

