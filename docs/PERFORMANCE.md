# Glance Warm-Path Performance

Measured on 2026-08-27 with Python 3.12.10 on the local Windows development environment.

## Method

- Endpoint: `GET /api/patients/{patient_id}`
- Transport harness: FastAPI/Starlette `TestClient`
- Adapter: in-memory repository
- Dataset: one synthetic patient, six timeline entries, three highlights and one section
- Warm-up: 100 requests
- Measured sample: 1,000 sequential requests
- Timing: wall-clock duration around each complete request/response

## Result

| Metric | Result |
| --- | ---: |
| Mean | 0.737 ms |
| P50 | 0.695 ms |
| P95 | 1.005 ms |
| Maximum | 8.141 ms |
| Prototype target | ≤ 300 ms P95 |

The measured prototype passes its warm-path target. This result does not include a network hop,
durable database, production authentication, concurrent load or a representative multi-patient
dataset, so it must not be used as a production capacity claim.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_glance.py --iterations 1000 --warmup 100
```
