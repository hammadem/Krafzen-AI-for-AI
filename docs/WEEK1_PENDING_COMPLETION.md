# Week 1 — Pending Completion Tracker

**Last updated:** 2026-06-06  
**Integration branch:** `feat/week1-kiruthika-architecture-foundation`  
**Week 2 branch (do not use for Week 1 fixes):** `feat/week2-integration`  
**Production merge PR:** [#53](https://github.com/KRAFZEN/KRAFZEN-AI-/pull/53) (`feat/week1-…` → `main`) — **hold until checklist below is done**

---

## How to use this doc

| Symbol | Meaning |
|--------|---------|
| ✅ | Done on integration branch |
| 🟡 | Partial / stub / needs verification |
| ❌ | Not done — Week 1 scope |
| ⏭️ | Explicitly Week 2+ (do **not** block Week 1 sign-off) |

**Where to commit Week 1 work:** `feat/week1-kiruthika-architecture-foundation` only.  
**After Week 1 sign-off:** merge #53 to `main`, then merge `main` into `feat/week2-integration`.

---

## Shared / cross-team (all 4)

| # | Task | Owner | Status | Notes |
|---|------|-------|--------|-------|
| S1 | Run Supabase migrations on shared project | **Kiruthika** | ❌ | See [Migration run order](#migration-run-order-kiruthika-only) |
| S2 | Smoke test: chat + DXF/IFC/DWG unchanged | **All** | ❌ | After migrations |
| S3 | Confirm lifecycle enums match everywhere | **All** | 🟡 | Code aligned; legacy job rows need `001` migration |
| S4 | Close superseded PRs **#50**, **#51** | **Kiruthika** | ❌ | Merged into week1 branch; ship via #53 only |
| S5 | Friday sign-off: contract + storage naming agreed | **Kiruthika** | 🟡 | Informal ack in standup; document decisions below |
| S6 | Merge week1 fixes into `feat/week2-integration` (daily if needed) | **Kiruthika** | 🟡 | After any week1 commit |

### Migration run order (Kiruthika only)

Apply in order on shared Supabase (coordinate with team; no intern runs prod DB):

1. `supabase/migrations/20260507183000_projects_add_image_and_dwg_urls.sql` — `image_url`, `dwg_url` on `projects`
2. `backend/app/db/migrations/001_align_job_status_to_contract.sql` — job status → contract values
3. `backend/app/db/migrations/002_week1_architecture_foundations.sql` — jurisdictions, compliance tables, `export_jobs`
4. `backend/app/db/migrations/003_workspace_tables.sql` — **optional for strict Week 1** (already in branch from Yehor; only run if you accept Week 2 workspace on shared DB now)

---

## Kiruthika (Lead) — Week 1 pending

### Done ✅

- Export lifecycle + validation contracts (`export_contracts.py`)
- Contract endpoints under `/api/v1/contracts/*`
- Migration `002_week1_architecture_foundations.sql`
- Unit tests: `backend/tests/unit/test_architecture_contracts.py`
- Integration branch merges (Sunny #50–52, Yehor #54, Tazwar queue/dashboard)

### Pending ❌ / 🟡

| # | Task | Priority | Branch |
|---|------|----------|--------|
| K1 | **Run migrations** (see S1) | P0 | N/A (Supabase) |
| K2 | **ExportModel schema draft** (geometry + metadata fields, JSON shape) | P0 | `feat/week1-…` | ✅ |
| K3 | **ADR set** (DXF/IFC-first, Revit phase 2, queue vs persistence split) | P1 | `docs/` on week1 | ✅ |
| K4 | Publish **one-page Week 1 sign-off** (what changed, what each intern starts Week 2) | P1 | Slack + optional `docs/` | ✅ |
| K5 | **Compliance domain narrative** (jurisdiction versioning strategy doc) | P1 | `docs/` | ✅ |
| K6 | Review & merge remaining week1 PRs; **merge week1 → week2** (daily if needed) | P0 | Both branches | 🟡 After this commit |
| K7 | **Merge PR #53 to `main`** only after full checklist | P0 | After K1–S2 | ❌ |
| K8 | Close PRs **#50**, **#51** with superseded comment | P2 | GitHub | 🟡 |
| K9 | Confirm `WEEK1_ARCHITECTURE_HANDOFF.md` shared with team (local copy OK if untracked) | P2 | — | ✅ |

### Week 1 sign-off checklist (from lead plan)

| Item | Status |
|------|--------|
| Shared contract endpoints reviewed by all 4 | 🟡 |
| Export lifecycle enums identical backend / worker / frontend | 🟡 |
| Validation payload sample accepted by Sunny | 🟡 |
| Storage artifact key naming accepted by Yehor + Tazwar | 🟡 |
| OpenAPI-ready contract summary published | ✅ |

---

## Yehor — Week 1 pending

### Done ✅

- Auth/profile stabilization (`/users/profile`, email fetch)
- Projects API: pagination, ownership, status filter
- Files API: metadata, ownership, delete/rename patterns
- `require_role` middleware scaffold
- Storage architecture doc (`storage-architecture.md`)
- Merged via PR #54 into week1 branch

### Pending ❌ / 🟡

| # | Task | Priority | Branch |
|---|------|----------|--------|
| Y1 | Remove **migration TODO stubs** in `project_queries.py` (`image_url`, `dwg_url` return `None`) after K1 runs | P0 | `feat/week1-…` | ✅ Code ready; verify after K1 |
| Y2 | **Baseline API contract doc** with sample payloads (projects, files, profile, jobs) | P1 | `backend/docs/` | ✅ |
| Y3 | **401/403 response shape** consistent across routes (audit + fix stragglers) | P1 | `feat/week1-…` | ✅ Jobs + profile routes |
| Y4 | **Role from DB** — currently stub `"member"` in `user_routes.py` / `permissions.py` | 🟡 | **Week 1:** document stub; **real RBAC:** ⏭️ Week 2 with `003` | ✅ Documented |
| Y5 | Align **storage path conventions** with Tazwar (written ack in PR or doc) | P1 | Comment in Y2 doc | ✅ |
| Y6 | Verify **no route mismatch** vs `frontend/lib/api/api.ts` (grep + quick manual test) | P0 | `feat/week1-…` | ✅ Audit doc + path fixes |

### Do not count as Week 1 gaps (already on branch, Week 2 scope)

| Item | Note |
|------|------|
| Workspace APIs + `003_workspace_tables.sql` | ⏭️ Week 2 — already merged early; don’t expand scope for Week 1 sign-off |
| `GET /api/v1/exports`, `/templates`, `archived` projects | ⏭️ Week 2 per guides |

---

## Tazwar — Week 1 pending

### Done ✅

- `queue_service.py` — lifecycle transitions aligned to `ExportStatus`
- Job routes wired (`enqueue`, `advance`, `retry`)
- `001_align_job_status_to_contract.sql`
- Dashboard: activity, notifications, workspace summary, members, queue health
- `monitoring_architecture.md`, `queue_monitor.py`
- Tests: `test_queue_service.py`, `test_dashboard.py`

### Pending ❌ / 🟡

| # | Task | Priority | Branch |
|---|------|----------|--------|
| T1 | **Event taxonomy doc** (`project.*`, `file.*`, `export.*`, `validation.*`, `notification.*`) | P1 | `backend/docs/event_taxonomy.md` |
| T2 | **Event payload schema** sample JSON (1–2 examples per family) | P1 | Same doc or comment in `dashboard_routes.py` |
| T3 | Verify **structured logs** include `job_id` on all paths after migration `001` | P1 | `feat/week1-…` |
| T4 | **Manual test:** create job → advance through states → retry from `failed` | P0 | Post-migration |
| T5 | Confirm **notification mark-read** path matches Sunny (`dashboard` routes) | P2 | `feat/week1-…` |
| T6 | Storage naming **ack** with Yehor (for artifact handoff Week 2) | P1 | Comment / doc |

### Explicitly Week 2 (not Week 1 blockers)

| Item | Note |
|------|------|
| Export **worker** executing DXF/IFC/DWG | ⏭️ Week 2 |
| Notifications **persistence table** | ⏭️ Week 2 (`dashboard_routes.py` comments) |

---

## Sunny — Week 1 pending

### Done ✅

- Design system tokens/utilities (merged via week1 integration)
- Projects dashboard: real API, skeletons, empty/error states
- Activity + notifications wired to dashboard APIs
- Exports/templates pages: contract-aligned format filters, `useApiResource`
- Billing wired to subscription data
- Merged via PR #52 (+ #50/#51 content on integration branch)

### Pending ❌ / 🟡

| # | Task | Priority | Branch |
|---|------|----------|--------|
| SU1 | **Fix 3 failing tests** — wrap with `AuthProvider` or mock `useAuth` | P0 | `feat/week1-…` |
| | `__tests__/dashboard/Billings.test.tsx` | | |
| | `__tests__/dashboard/Exports.test.tsx` | | |
| | `__tests__/dashboard/Projects.test.tsx` | | |
| SU2 | **API route audit** — document pages still on empty/pending endpoints | P1 | Comment or short `frontend/docs/week1-api-wiring.md` |
| SU3 | Exports page: confirm **graceful empty state** until `/api/v1/exports` exists (Week 2) | P2 | Already mostly done |
| SU4 | **ProtectedUI / permission gates** — not started | 🟡 | **Minimal Week 1:** hide/disable by role stub; full gates ⏭️ Week 2 |
| SU5 | **Centralized error normalization** in `lib/api/api.ts` (401 → login, 403 message) | P1 | `feat/week1-…` |
| SU6 | Confirm **validation template** shape with Kiruthika (read from `/contracts/validation-template`) | P2 | No UI required Week 1 |
| SU7 | Run `npm test` + `npm run lint` clean before week1 sign-off | P0 | Local |

### Pages with pending backend (OK for Week 1 if empty state works)

| Page | Backend | Week 1 expectation |
|------|---------|-------------------|
| Exports | `GET /api/v1/exports` | Empty state + filters only |
| Templates | `GET /api/v1/templates` | Empty state |
| Archive | `archived=true` on projects | Empty state |

---

## Suggested 2-day finish order

### Day 1

| Who | Focus |
|-----|--------|
| **Kiruthika** | K1 migrations → S2 smoke test → K2 ExportModel draft |
| **Yehor** | Y1 after migrations, Y6 route audit, start Y2 |
| **Tazwar** | T4 manual job flow after `001`, T1 taxonomy doc |
| **Sunny** | SU1 fix tests, SU5 error handling |

### Day 2

| Who | Focus |
|-----|--------|
| **Kiruthika** | K3 ADR, K4 sign-off, K7 prep (#53), S4 close #50/#51 |
| **Yehor** | Y2 API doc, Y3/Y5 |
| **Tazwar** | T2 payloads, T6 ack |
| **Sunny** | SU2 audit doc, SU7 green CI locally |

---

## Definition of “Week 1 complete”

All must be true before merging **PR #53** to `main`:

- [ ] Migrations applied on shared Supabase (K1)
- [ ] Smoke test passed (S2)
- [ ] Frontend tests pass (SU1, SU7)
- [ ] Backend tests pass (`pytest` on week1 branch)
- [ ] ExportModel draft + ADR published (K2, K3)
- [ ] Event taxonomy doc published (T1)
- [ ] API contract doc published (Y2)
- [ ] Sign-off checklist table above all ✅ or explicitly deferred with owner + Week 2 date
- [ ] PRs #50 and #51 closed
- [ ] Team notified: Week 2 work targets `feat/week2-integration`

---

## Branch & PR quick reference

| Branch / PR | Purpose |
|-------------|---------|
| `feat/week1-kiruthika-architecture-foundation` | Week 1 fixes only |
| `feat/week2-integration` | All new Week 2 features |
| PR **#53** | Week 1 → `main` (open until sign-off) |
| PR **#50**, **#51** | Close (superseded) |
| PR **#52**, **#54** | Already merged into week1 |

---

## Contacts / ownership (Week 1 close-out)

| Area | DRI |
|------|-----|
| Migrations & Supabase | Kiruthika |
| Contracts & ExportModel | Kiruthika |
| Auth / projects / files APIs | Yehor |
| Queue / dashboard / monitoring | Tazwar |
| Frontend integration & tests | Sunny |

*Update this doc as items close; strike through or change ❌ → ✅ in PR descriptions when merging.*
