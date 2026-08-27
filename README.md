# Nightingale Care Note

A provenance-first longitudinal care note prototype for a single synthetic patient. The project
helps clinical staff understand urgent information quickly while keeping AI-generated content,
human-authored notes, source evidence, and access boundaries explicit.

> This repository contains synthetic demonstration data only. It is not a medical device and is
> not ready for production use.

## Current capabilities

- A 10-second Glance view with prioritized highlights, risk reasons, suggested actions, and
  review states.
- An actionable highlight workflow with care-role assignment, open/in-progress/completed states,
  disposition notes, optimistic concurrency checks, and metadata-only audit events.
- A longitudinal timeline containing patient, staff, clinician, and three distinct AI-scribed
  entry types.
- Role-authored manual timeline notes whose server-generated author and entry type cannot be
  forged by the browser.
- Clinician-created highlights from an exact selected source span, with risk reason, suggested
  action, priority, assignment, and audit metadata.
- Exact highlight provenance pointers that resolve to an entry and character span.
- Exact source-span highlighting in the timeline and clinician/staff/patient demo-role switching.
- Server-side clinic scope, role ownership, and patient self-access checks.
- Patient-facing filtering that excludes internal highlights and raw AI-scribed entries.
- A patient-facing dashboard with explicitly published clinician-confirmed guidance, action
  progress, and a form for adding patient-authored symptom or question updates.
- Deterministic section versioning, audit metadata, revert behavior, and optimistic concurrency
  checks.
- Internal care-team comments with reply links, role mentions, assignment, and resolve/reopen.
- Editable clinician plan with API-backed revision history and revert controls.
- An in-page metadata-only audit trail for note creation, comments/replies, resolve/reopen,
  highlight assignment/completion/review, plan edits, and reverts.
- A tested PHI redaction gateway for any future external model adapter.
- Deterministic synthetic data for repeatable demonstrations and tests.
- Responsive, English-only web interface with loading, empty, forbidden, not-found, and error
  states.

## Technology

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic domain models
- Vanilla HTML, CSS, and JavaScript
- Pytest and Ruff

The current repository adapter stores data in memory. Restarting the process resets the dataset.

## Quick start

Create a virtual environment and install the application with development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Start the development server with automatic reload:

```powershell
.\.venv\Scripts\python.exe -m uvicorn nightingale.main:app --reload
```

Open:

- Application: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/api/health`

## Synthetic demo identity

The frontend can switch among fixed synthetic clinician, staff, and patient identities:

| Entity | ID |
| --- | --- |
| Clinic | `10000000-0000-4000-8000-000000000001` |
| Patient | `20000000-0000-4000-8000-000000000001` |
| Staff | `30000000-0000-4000-8000-000000000001` |
| Clinician | `40000000-0000-4000-8000-000000000001` |

The header-based identity mechanism is a development seam only. It must not be treated as
production authentication.

## Verification

Run the complete automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run static and formatting checks:

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
node --check src/nightingale/static/api.js
node --check src/nightingale/static/app.js
.\.venv\Scripts\python.exe scripts\benchmark_glance.py --iterations 1000 --warmup 100
```

The required acceptance scenarios are organized in:

- `tests/test_rbac_scope.py`
- `tests/test_revision_history.py`
- `tests/test_highlight_provenance.py`
- `tests/test_concurrent_edits.py`

Additional tests cover the synthetic dataset, patient API, and frontend/API contract.

## Architecture and trust boundaries

HTTP requests enter through the API layer and then pass to the service layer, where clinic scope,
role ownership, authorship, concurrency, and provenance rules are enforced. Repository adapters
handle persistence. The browser UI is not a security boundary.

Highlights contain a `risk_reason`, `suggested_action`, review status, and a
`provenance_pointer`. The repository rejects pointers that do not resolve to the same patient's
timeline or whose character span lies outside the source entry.

See `docs/ARCHITECTURE.md` for the current architecture and production direction.

## Security and privacy status

Implemented in the prototype:

- Synthetic data only.
- Server-side clinic scope and role ownership checks.
- Patient self-access restriction.
- Patient response filtering for internal and raw AI content.
- Full section snapshots and diffs, with a separate metadata-only audit event stream.
- Deterministic PHI redaction gateway for future LLM adapters.
- Reproducible Glance benchmark: 0.990 ms warm-path P95 in the recorded local run.

Required before production:

- Replace development headers with verified signed identity tokens.
- Replace the in-memory adapter with PostgreSQL and database RLS.
- Add TLS, encryption at rest, secret management, retention policies, and production audit
  controls.
- Repeat Glance load testing with a production-like database, network, concurrency, and
  representative dataset; the local in-memory result is not a capacity claim.

No external LLM is connected in the current scaffold, so no patient content is sent to a model.

## Project layout

```text
src/nightingale/
├── api/           HTTP routes and response handling
├── core/          Application configuration
├── data/          Deterministic synthetic seed data
├── domain/        Domain models and API contracts
├── repositories/  Persistence adapters
├── services/      Use cases and policy enforcement
└── static/        Patient web interface
tests/             Automated acceptance and integration tests
docs/              Architecture and development documentation
```

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT.md`
- `docs/TECHNICAL_BRIEF.md`
- `docs/DEMO_SCRIPT.md`
- `docs/DELIVERY_CHECKLIST.md`
- `docs/PERFORMANCE.md`
- `ATTRIBUTION.txt`

## License

Licensed under the MIT License. See `LICENSE`.
