# Data Sources — instrumentation-audit

Cross-system audit of **product/analytics instrumentation gaps**, system-by-system. Goal: name the metrics a PM needs but cannot compute today, and the events/properties required to plug them. Engineering system-health metrics are explicitly out of scope.

## Scope & method
- **System #1 = Serviceability** (this pass). Future systems (Allocation, Promise Engine, etc.) reuse the same framework.
- Gaps derived **first-principles** from each system's description doc. Every "Current state" label is a **hypothesis** until a live grounding audit confirms it.
- **Deferred grounding pass (not yet done):** audit the live Mixpanel event taxonomy + relevant Redshift instrumentation (`delivery_date_tracker.metadata.instrumentation_details`, `logistics_allocation_audit`) to flip each `Missing`/`Partial` to confirmed before any event is built.

## Sources

| Source | Description | Location |
|---|---|---|
| Serviceability Google Doc | System-of-record description of how serviceability works (3 decisions, MFC/FC inventory logic, hyperlocal vs courier, Clickpost config). Read 2026-06-18. | Google Drive doc `1xFwty65UVdMsl8NxNYXW7bdf1o8znGoUDFDI_4_-UxU` |
| Serviceability system snapshot | Self-contained copy of the above for analysis | `context/2026-06-18-serviceability-system-description-v1.md` |
| Instrumentation-gap framework | Reusable six-lens method applied per system | `context/2026-06-18-instrumentation-gap-framework-v1.md` |
| Repo schema reference | Confirmed current instrumentation is order-time / backend-promise-focused | `context/schema.md` (global) — `delivery_date_tracker`, `logistics_allocation_audit` |

## Deliverables
- `insights/2026-06-18-serviceability-instrumentation-gaps-v1.md` — Serviceability gap catalog (20 metrics, P0–P3).
