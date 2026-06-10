# Frontend ↔ Backend Route Audit (Week 1 — Y6)

**Audited:** `frontend/lib/api/api.ts` vs registered FastAPI routes  
**Branch:** `feat/week1-kiruthika-architecture-foundation`

## Fixed on week1 branch ✅

| Frontend call | Was | Correct backend path |
|---------------|-----|----------------------|
| `getAFile` / `updateAFile` | `/api/v1/jobs/files/{id}` | `/api/v1/files/{id}` |
| `updateAProject` | `/api/v1/jobs/projects/{id}` | `/api/v1/projects/{id}` |

## Aligned ✅

| Frontend | Backend |
|----------|---------|
| `POST /api/v1/files` | `file_routes` |
| `GET /api/v1/files?job_id=` | `file_routes` |
| `DELETE /api/v1/files/{id}` | `file_routes` |
| `POST/GET/PATCH/DELETE /api/v1/jobs` | `job_routes` |
| `POST/GET/PATCH/DELETE /api/v1/projects` | `project_routes` |
| `GET /api/v1/users/profile` | `user_routes` (AuthContext) |
| Dashboard URLs | `dashboard_routes` |

## Known gaps (Week 2 — empty UI OK for Week 1)

| Frontend | Backend | Note |
|----------|---------|------|
| `GET /api/v1/exports?user_id=` | Not implemented | Sunny empty state |
| `GET /api/v1/templates` | Not implemented | Sunny empty state |
| `GET /api/v1/projects?archived=true` | No `archived` filter yet | Use `status` or Week 2 flag |
| `GET /api/v1/projects?user_id=` | Ignored extra param | Auth token scopes user |

## Yehor follow-up

- [ ] Quick manual smoke: create project → create job → create file → GET file by id
- [ ] After K1 migration: verify `image_url` / `dwg_url` round-trip on `PATCH /projects/{id}`
