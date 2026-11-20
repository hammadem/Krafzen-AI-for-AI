# KRAFZEN AI — Production readiness validation (2026-11-18)

## Decision
**NOT PRODUCTION READY.** The combined fixes have automated verification, but the 31-page project PDF requires all 14 product modules and five end-to-end QA journeys. These are not implemented and verified in their entirety.

### Evidence recorded
- Branch: `fix/integration-p0-20261117`; PR #3 residency, PR #4 paid-only, PR #5 exports.
- Backend: **206 tests passed** and 44 warnings on `c325152f`; actual Potrace image-to-DXF smoke test included in CI.
- Frontend: **22 tests passed**, TypeScript compilation passed on `36571a3b`.
- Supabase project `Krafzen-AI` reports region `us-east-1` and **INACTIVE** as of 2026-11-18; no live schema, storage, billing or residency verification possible.
- Render service/region inspection requires user-selected workspace.
- No production database migrations applied; no staging or production deployment performed; main unchanged.

## Security hardening completed
- Server-side paid access (zero free credits) and active-status entitlement checking; migration prepared, not applied.
- Conditional paid-request decrement to reject stale concurrent balance writes.
- Conditional export job status transitions to prevent duplicate queued-job claims.
- Client export-status PATCH denied; exact artifact is signed instead of most recent file with same extension.
- Bounded inline image input only for DXF tracing; rejects remote URL SSRF entry point. Remote-image consumers must switch to a controlled authenticated asset flow.
- Frontend unknown roles no longer default to owner. Backend role enforcement still requires review.
- DXF tracing uses real Potrace with readable entities; DWG uses ODA but has not been tested against a live installed converter. Neither provides guaranteed CAD dimensional accuracy.
- IFC/Revit output unavailable. US-sovereign exports blocked until regional metadata/storage/source reads are verified.

## Mandatory production gates
1. **Supabase & residency:** activate isolated staging project, apply reviewed migrations to staging, verify RLS, tenants, US DB/storage/backups, worker region, logs, AI-provider processing and audit records.
2. **Payments:** sandbox checkout with verified webhooks; lifecycle, replays, duplicates, upgrades, cancel, refunds, failed/late invoices, subscription status and concurrent quota consumption. Reconcile provider state to DB state.
3. **CAD:** run varied real architectural sample drawings through Potrace/ODA, inspect results in independent DWG/DXF viewers, validate units, layers, scale, signed artifacts and job failures. Implement genuine IFC/Revit before enabling those outputs.
4. **Roles/security:** exercise cross-account and cross-org access through actual SQL/RLS and storage; fix all untrusted URL entry points, secret exposures and severe npm advisories.
5. **Reliability:** real distributed worker leases, stuck-job recovery, idempotent settlement, backup restore and load testing; staging deployment approval.
6. **Product scope:** verify Projects, Archive, Activity, Exports, Members, Notifications, Billing, Imports, Reviews & Redlines, BIM (IFC), As-Built, IBC/NFPA Compliance, Field, and USA Data Residency. Many remain unimplemented or only partial.
7. **PDF acceptance:** execute the five full flows for residential architecture, commercial, BIM, as-built revision, and paid customer, using multiple persisted sample projects; capture QA evidence and reviewer sign-off.

## No-go rule
Do not merge to production main, claim construction-grade engineering correctness, or enable sovereign exports based on unit tests alone.
