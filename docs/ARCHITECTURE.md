# Architecture

Requests enter through the API layer, which parses HTTP input before calling the service layer.
The service layer enforces RBAC, clinic scope, section ownership, concurrency, and provenance
rules. Repository adapters handle persistence. The UI is never treated as a security boundary.

`InMemoryCareNoteRepository` is intended only for rapid development and unit tests. The
production path uses PostgreSQL, with `clinic_id` present on every patient-scoped table and both
database RLS and service policies restricting access.

Any external LLM adapter must sit behind the tested `PHIRedactionGateway`; no external LLM is
connected in this prototype. Logs may contain only
safe metadata such as request IDs, latency, and redaction counts; they must never contain patient
content.
