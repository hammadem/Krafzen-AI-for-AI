# Week 1 Baseline API Contracts (Yehor)

**Owner:** Yehor · Base path `/api/v1`  
**Error shape (401/403/4xx on Yehor-owned routes):** `{"detail": {"error": "<message>"}}`  
**Auth:** `Authorization: Bearer <supabase_jwt>` → middleware returns `{"user_id": "<uuid>"}`

---

## Role stub (Week 1 — Y4)

Real RBAC ships Week 2 with `003_workspace_tables.sql`. Until then:

- `GET /users/profile` returns `get_role_payload("member")` — hardcoded role
- `require_role` middleware uses the same stub
- Frontend should treat `role`, `can_write`, `can_delete` as **informational only**

---

## Storage naming ack (Week 1 — Y5, aligned with Tazwar)

| Bucket | Path | Owner |
|--------|------|--------|
| `dxf-files` | `{user_id}/{project_id}/{filename}` | Tazwar (CAD artifacts) |
| `krafzen-files` | `{user_id}/{project_id}/{file_id}.{ext}` | Yehor (user uploads) |

Project URL fields (`dxf_url`, `dwg_url`, `image_url`) are set via `PATCH /projects/{id}` after Tazwar upload.  
`files` table stores metadata; `artifact_file_id` on `export_jobs` links exports (Week 2).

See `backend/docs/storage-architecture.md`.

---

## Projects

### `POST /projects`

Request:

```json
{
  "input_text": "3-bedroom ranch, IRC baseline"
}
```

Response `201`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "auth-user-uuid",
  "input_text": "3-bedroom ranch, IRC baseline",
  "parsed_json": null,
  "image_url": null,
  "dxf_url": null,
  "dwg_url": null,
  "created_at": "2026-05-28T12:00:00Z",
  "updated_at": null
}
```

### `GET /projects?page=1&limit=10&status=active`

Response `200`: array of `ProjectOut` (auth-scoped; `user_id` query param from frontend is ignored — token is source of truth).

### `GET /projects/{project_id}`

Response `200`: single project. `403` if not owner: `{"detail": {"error": "Access denied"}}`.

### `PATCH /projects/{project_id}`

Request (partial):

```json
{
  "dxf_url": "https://...supabase.co/storage/v1/object/public/dxf-files/user/project/file.dxf",
  "dwg_url": "https://.../file.dwg",
  "image_url": "https://.../preview.webp"
}
```

---

## Files

### `POST /files`

Request:

```json
{
  "job_id": "job-uuid",
  "project_id": "project-uuid",
  "file_type": "dxf",
  "path": "user_id/project_id/project_xyz_20260528.dxf",
  "bucket": "dxf-files",
  "mime_type": "application/dxf",
  "size_bytes": 4096
}
```

Response `201`: `FileResponse` with `id`, `job_id`, `bucket`, `path`, etc.

### `GET /files?job_id={job_id}`

Response `200`: `FileResponse[]`

### `GET /files/{file_id}` · `PATCH /files/{file_id}` · `DELETE /files/{file_id}`

Standard CRUD; ownership enforced via job → project chain.

---

## Jobs

### `POST /jobs`

Request:

```json
{
  "project_id": "project-uuid",
  "status": "queued",
  "transcript": "Optional notes"
}
```

Response `201`:

```json
{
  "id": "job-uuid",
  "project_id": "project-uuid",
  "status": "queued",
  "transcript": "Optional notes",
  "error_message": null,
  "created_at": "2026-05-28T12:00:00Z",
  "updated_at": null
}
```

Status values: see `GET /contracts/export-lifecycle`.

### `POST /jobs/{job_id}/advance` · `POST /jobs/{job_id}/retry`

Owned by Tazwar (queue service); Yehor persistence only creates/reads base rows.

---

## Profile

### `GET /users/profile`

Response `200`:

```json
{
  "id": "auth-user-uuid",
  "email": "user@example.com",
  "role": "member",
  "is_admin": false,
  "can_write": true,
  "can_delete": false,
  "plan_tier": "trial",
  "remaining_minutes": 120,
  "total_minutes_purchased": 0,
  "subscription_status": "active",
  "plan_requests_remaining": 10,
  "trial_requests_remaining": 3
}
```

---

## Week 2 endpoints (not Week 1 blockers)

| Endpoint | Status |
|----------|--------|
| `GET /exports` | Week 2 |
| `GET /templates` | Week 2 |
| `GET /projects?archived=true` | Week 2 |

See `backend/docs/FRONTEND_API_ROUTE_AUDIT.md` for frontend wiring status.
