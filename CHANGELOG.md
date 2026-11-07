# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- ISO file format validation: `validate_iso_file()` function checks for ISO 9660 (CD001) or UDF (BEA01) signatures at sector 16
- Upload endpoint now rejects non-ISO files with 400 Bad Request before metadata extraction
- Test fixture for valid ISO content to enable reliable testing

### Fixed
- ISO parser tests now correctly expect marketing version strings (e.g., "24H2") from `parse_version_string()`

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this format.

## [1.0.0] - 2026-10-15

### Added
- FastAPI backend with SQLite + SQLAlchemy persistence
- React + TypeScript + Vite frontend with dark theme
- ISO upload with SHA256 deduplication and metadata storage
- ISO metadata extraction (version, edition, build number, architecture, language) from Windows ISOs using WIM parsing
- Build recipe CRUD with JSON schema validation (components, removals, registry tweaks, unattend snippets)
- Recipe cloning and versioning
- Build job orchestration with stage tracking (pending → mounting → inventory → component_cleanup → registry_tweaks → unmounting → iso_creation → completed/failed)
- Progress tracking and persistent build logs
- Demo authentication mode for local development
- OIDC/Keycloak integration ready (profile: with-auth)
- Docker Compose with backend, frontend, and Keycloak services
- Health checks for all services
- Comprehensive test suite (backend pytest, frontend vitest)
- Responsive UI with loading/error/empty states

### Security
- Demo mode restricted to localhost
- No hardcoded credentials
- .env.example with blank secrets
- .gitignore excludes .env, databases, build artifacts

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
