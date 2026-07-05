# Production deployment checklist

## 1. Back up Supabase

Start Docker Desktop, then run from the repository root:

```bash
./scripts/backup-supabase.sh
```

The command creates timestamped `roles.sql`, `schema.sql`, `data.sql`, and local-compatible `data.local.sql` files under `backups/supabase/`, verifies that they are non-empty, and writes SHA-256 checksums. The local copy excludes Supabase-managed Auth and Storage data to avoid service-version schema conflicts; create local test users instead. Copy the resulting directory to encrypted off-site storage before deployment.

This logical backup contains database records, including Auth and Storage metadata. It does **not** contain the actual bytes stored in Supabase Storage buckets. Export important bucket objects separately.

## 2. Apply Week 2 migrations

After verifying the backup and before deploying application code, apply the reviewed migrations in order:

```bash
SUPABASE_DATABASE_URL='<production pooler or direct database URL>' ./scripts/apply-week2-migrations.sh
```

The guarded runner applies `002` through `008`, then enables RLS on every newly exposed table. Do not run it until the backup has been copied to encrypted off-site storage.

## 3. Restore production data locally

The local Supabase CLI stack requires Docker and `psql`. The restore is destructive only to the local database on port `54322`.
The restore starts a clean managed Supabase database and intentionally bypasses repository migrations because the production schema is supplied by the backup.

```bash
./scripts/restore-supabase-local.sh backups/supabase/<timestamp>
npx supabase status
```

Update local runtime variables using the values printed by `supabase status`:

```dotenv
SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

Use the local anon and service-role keys printed by `supabase status`; never put the service-role key in a `NEXT_PUBLIC_*` variable.

Production data may contain personal information. Keep local copies encrypted, restrict access, and delete them after validation.

## 4. Validate the application

```bash
cd frontend
npm ci
npm run lint
npm test -- --run
npm run build

cd ../backend
./venv/bin/python -m pytest -q
```

Start both services and test `/health`, authentication, project creation, chat, file upload, export generation, billing callbacks in test mode, and authorization boundaries between two test users.

## 5. Check production configuration

- Vercel must have `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and the production backend URL for every intended environment.
- Render must have all variables listed in `backend/render.yaml`, plus `SUPABASE_DATABASE_URL` if runtime code requires direct PostgreSQL access.
- `ALLOWED_ORIGINS` must include the exact Vercel production domain.
- Supabase Auth Site URL and redirect allow-list must include the production Vercel domain and callback URL.
- Stripe must remain in test mode until webhook delivery and signature validation pass.
- Confirm the Render health check path matches the implemented endpoint.

## 6. Deploy safely

Deploy to staging first, run smoke tests against staging, then promote the same commit to production. Do not run `supabase db reset --linked`; it destroys the linked remote database.

After deployment, verify the frontend, Render `/health`, authentication callback, database reads/writes, Storage uploads, background/export work, CORS, and error monitoring. Keep the pre-deployment backup until production has been stable for the agreed retention period.
