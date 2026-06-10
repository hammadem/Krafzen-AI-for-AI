# Week 1 — Frontend API Wiring Audit (SU2)

Which dashboard pages are wired to which backend endpoints, and which are
still waiting on a pending/empty endpoint. Pages waiting on an endpoint
degrade gracefully to a loading → empty/error state (no crash).

_Owner: Sunny (frontend). Last updated: Week 1 sign-off._

## Status legend
- ✅ **Live** — endpoint exists and returns data
- 🟡 **Partial** — endpoint live but returns limited data in Week 1
- 🔴 **Pending** — endpoint not deployed yet; page shows empty/error state

| Page | Route | Endpoint | Status | Owner | Notes |
|------|-------|----------|--------|-------|-------|
| Projects | `/projects`, `/workspace/projects` | `GET /api/v1/projects?user_id=&page=&limit=` | ✅ Live | Yehor | Paginated (length-based has_more). |
| Project detail | `/workspace/id/[slug]` | `GET /api/v1/projects/{id}` | ✅ Live | Yehor | |
| Create project | (workspace) | `POST /api/v1/projects` | ✅ Live | Yehor | Optimistic + rollback. |
| Activity | `/workspace/activity` | `GET /api/v1/dashboard/activity` | 🟡 Partial | Tazwar | Auth-scoped; payload shape being finalized. |
| Members | `/workspace/members` | `GET /api/v1/dashboard/members` | 🟡 Partial | Tazwar | Week 1 returns authed user as owner only. |
| Workspace summary | `/workspace/members` (stats) | `GET /api/v1/dashboard/workspace-summary` | 🟡 Partial | Tazwar | Non-critical; hidden if absent. |
| Notifications | `/workspace/notifications` | `GET /api/v1/dashboard/notifications` | 🟡 Partial | Tazwar | Supports `unread_only`, `limit`; mark-as-read via PATCH. |
| Templates | `/workspace/templates` | `GET /api/v1/templates` | 🔴 Pending | Yehor | Empty state until endpoint ships. |
| Exports | `/workspace/exports` | `GET /api/v1/exports` | 🔴 Pending | Kiruthikha | Empty state; enriched in Week 2 (statuses/retry). |
| Archive | `/workspace/archive` | `GET /api/v1/projects?archived=true` | 🔴 Pending | Yehor | Needs `archived` flag on projects. |
| Billing | `/workspace/billings` | (Supabase user fields) | ✅ Live | — | Plan/credits from session; history pending. |
| Settings | `/workspace/settings` | (Supabase user) | ✅ Live | — | |

## Pending endpoints blocking full data (not frontend work)
- `GET /api/v1/templates` — Yehor
- `GET /api/v1/exports` — Kiruthikha (Week 2)
- `archived=true` projects filter — Yehor

## Error handling (SU5)
Auth/permission failures are normalized centrally in `lib/api/utils.ts`:
- **401** → `AUTH` error + redirect to `/login`
- **403** → clear "no permission" message
- other 4xx/5xx → `APIERROR` with server detail
