# Development and Operation

## Requirements

- Python 3.11 or later
- Data currently lives only in memory and is cleared when the process restarts. This adapter is
  not production storage.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Start the application

```powershell
uvicorn nightingale.main:app --reload
```

Open `http://127.0.0.1:8000`. Interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

## Synthetic demo API

The development dataset uses fixed IDs so tests and demos are reproducible:

- Patient: `20000000-0000-4000-8000-000000000001`
- Clinic: `10000000-0000-4000-8000-000000000001`
- Clinician: `40000000-0000-4000-8000-000000000001`

```powershell
$headers = @{
  "x-actor-id" = "40000000-0000-4000-8000-000000000001"
  "x-actor-role" = "clinician"
  "x-clinic-id" = "10000000-0000-4000-8000-000000000001"
}
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/patients/20000000-0000-4000-8000-000000000001" `
  -Headers $headers
```

These headers are a development identity seam, not a production authentication design.

## Verification

Run the automated test suite and static checks directly:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
node --check src/nightingale/static/api.js
node --check src/nightingale/static/app.js
```

## Current security boundary

`CareNoteService` enforces clinic scope, actor identity, and section ownership. Header-based
identity is only a development seam. It must be replaced with middleware that verifies signed
tokens, and database RLS must be added before production use. All tests and demonstrations must
use synthetic data.

## Directory responsibilities

```text
src/nightingale/
├── api/           HTTP input and output; contains no authorization policy
├── core/          Configuration and cross-cutting concerns
├── data/          Deterministic synthetic development data
├── domain/        Domain models and stable data contracts
├── repositories/  Persistence ports and adapters
├── services/      Use cases, RBAC, conflict, and provenance rules
└── static/        Lightweight single-patient web interface
tests/             Automated domain, authorization, API, and UI contract tests
docs/              Architecture and development documentation
```
