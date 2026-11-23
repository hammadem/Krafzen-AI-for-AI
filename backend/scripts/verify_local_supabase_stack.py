"""Smoke-test an isolated Supabase Auth/REST/Storage/DB local test stack.

Reads ONLY temporary credentials emitted by 'supabase status --output json'
inside GitHub Actions, never the remote KRAFZEN cloud project.
"""
import json
import os
from pathlib import Path
from urllib.parse import urljoin

import psycopg2
import requests


def main() -> None:
    info = json.loads(Path(os.environ["LOCAL_SUPABASE_STATUS_FILE"]).read_text())
    api = info.get("PROJECT_URL") or info.get("API_URL") or info.get("API")
    key = info.get("SERVICE_ROLE_KEY") or info.get("SECRET_KEY")
    anon = info.get("ANON_KEY") or info.get("PUBLISHABLE_KEY")
    db_url = info.get("DB_URL")
    assert isinstance(api, str) and api.startswith("http://127.0.0.1:")
    assert isinstance(key, str) and len(key) > 10
    assert isinstance(db_url, str) and db_url.startswith("postgresql://")
    base = api.rstrip("/") + "/"

    # Validate that the entire committed migration set can bootstrap a new
    # database with all critical engineering and payment tables.
    with psycopg2.connect(db_url) as connection:
        with connection.cursor() as cur:
            cur.execute("""
                select
                    to_regclass('public.projects') is not null,
                    to_regclass('public.files') is not null,
                    to_regclass('public.field_photos') is not null,
                    to_regclass('public.drawing_redlines') is not null,
                    to_regclass('public.asbuilt_comparisons') is not null,
                    to_regclass('public.compliance_assessments') is not null,
                    to_regclass('public.export_jobs') is not null
            """)
            verified = cur.fetchone()
            assert all(verified), f"Missing post-migration tables: {verified}"
            cur.execute("""
                select relrowsecurity from pg_class
                where oid = 'public.field_photos'::regclass
            """)
            assert cur.fetchone()[0] is True, "Private field photos need RLS"
            cur.execute("""
                select count(*) from supabase_migrations.schema_migrations
            """)
            total = cur.fetchone()[0]
            assert total >= 10, f"Unexpectedly few committed migrations: {total}"

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    # Validate actual local Data API gateway and private Storage without any
    # customer-owned data or changes to the connected remote project.
    health = requests.get(urljoin(base, "rest/v1/"), headers=headers, timeout=20)
    assert health.status_code in (200, 404), (
        "REST gateway is unavailable", health.status_code
    )
    auth = requests.get(urljoin(base, "auth/v1/settings"), headers=headers, timeout=20)
    assert auth.status_code == 200, (
        "Local GoTrue auth service unavailable", auth.status_code
    )

    bucket = "krafzen-ci-private"
    create = requests.post(
        urljoin(base, "storage/v1/bucket"),
        headers={**headers, "Content-Type": "application/json"},
        json={"id": bucket, "name": bucket, "public": False},
        timeout=25,
    )
    assert create.status_code in (200, 201), (
        "Could not create isolated private storage bucket",
        create.status_code, create.text[:200],
    )
    content = b"krafzen-ci-storage-object\n"
    relative = f"storage/v1/object/{bucket}/known.txt"
    saved = requests.post(
        urljoin(base, relative),
        headers={
            **headers, "Content-Type": "text/plain",
            "x-upsert": "false",
        },
        data=content,
        timeout=20,
    )
    assert saved.status_code in (200, 201), (
        "Isolated storage PUT failed", saved.status_code, saved.text[:200]
    )
    downloaded = requests.get(urljoin(base, relative), headers=headers, timeout=20)
    assert downloaded.status_code == 200 and downloaded.content == content

    signed = requests.post(
        urljoin(base, f"storage/v1/object/sign/{bucket}/known.txt"),
        headers=headers, json={"expiresIn": 60}, timeout=20,
    )
    assert signed.status_code == 200 and (
        signed.json().get("signedURL") or signed.json().get("signedUrl")
    ), ("Private object signed URL unavailable", signed.status_code)

    if anon:
        forbidden = requests.get(
            urljoin(base, relative),
            headers={"apikey": anon, "Authorization": f"Bearer {anon}"},
            timeout=20,
        )
        assert forbidden.status_code in (400, 401, 403, 404), (
            "Anonymous key can read restricted private objects!", forbidden.status_code
        )
    print(f"PASS: isolated local Supabase DB ({total} migrations), Auth, REST, private Storage, signed access")


if __name__ == "__main__":
    main()
