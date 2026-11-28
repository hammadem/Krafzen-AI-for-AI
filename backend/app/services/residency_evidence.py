from app.core.config import settings


def platform_evidence():
    # Operator records are bound to the actual project reference. A change
    # of endpoint invalidates the evidence instead of inheriting its location.
    project_matches = bool(
        settings.RESIDENCY_EVIDENCE_PROJECT_ID
        and settings.SUPABASE_PROJECT_ID == settings.RESIDENCY_EVIDENCE_PROJECT_ID
        and settings.SUPABASE_URL.rstrip("/") ==
            f"https://{settings.RESIDENCY_EVIDENCE_PROJECT_ID}.supabase.co"
        and settings.RESIDENCY_EVIDENCE_DATABASE_REGION == "us-east-1"
    )
    compute_matches = settings.RESIDENCY_EVIDENCE_RENDER_REGION == "virginia"
    location_state = "provider_region_recorded" if project_matches else "unverified"
    compute_state = "provider_region_recorded" if compute_matches else "unverified"
    return {
        "requested_region": "us",
        "residency_verified": False,
        "evidence_recorded_at": settings.RESIDENCY_EVIDENCE_RECORDED_AT or None,
        "paths": [
            {"name": "Primary database and Auth", "status": location_state,
             "location": "AWS us-east-1" if project_matches else None,
             "detail": "Provider project location; not a transfer guarantee."},
            {"name": "Primary file storage origin", "status": location_state,
             "location": "AWS us-east-1" if project_matches else None,
             "detail": "US origin only; object backups and CDN require separate review.", "source_url": "https://supabase.com/docs/guides/storage/cdn/fundamentals"},
            {"name": "Frontend and API compute", "status": compute_state,
             "location": "Render Virginia" if compute_matches else None,
             "detail": "Recorded service regions, not a continuous infrastructure attestation."},
            {"name": "Temporary files", "status": "unverified", "detail": "Confirm all processing and cleanup paths."},
            {"name": "Backups and recovery", "status": "unverified", "detail": "Verify backup coverage, retention, recovery and replication."},
            {"name": "Render service log storage", "status": compute_state, "location": "Render Virginia" if compute_matches else None, "detail": "Render documents regional log storage; external streams and platform access not verified.", "source_url":"https://render.com/docs/logging"},
            {"name": "Supabase logs and external log streams", "status":"unverified","detail":"Verify processing destinations, access, retention and forwarding."},
            {"name": "Storage CDN and downloads", "status":"unverified","detail":"Supabase documents global CDN caching. A US origin is not a US-only delivery or caching guarantee. Do not approve sovereign storage without an independently reviewed private path.", "source_url":"https://supabase.com/legal/privacy-resources/data-residency-and-transfers-faq"},
            {"name": "Background jobs", "status": "unverified", "detail": "Dedicated US worker execution and heartbeat not established."},
            {"name": "AI inference", "status": "unverified", "detail": "Local intent and browser symbol models do not require external inference. External provider processing jurisdiction remains unverified."},
            {"name": "Third-party integrations", "status": "unverified", "detail": "Auth, email, billing and other processors need review."},
            {"name": "Analytics and telemetry", "status": "unverified", "detail": "Verify all logging, analytics and error-reporting destinations."},
            {"name": "Dedicated tenant storage and routing", "status": "unverified", "detail": "Separate regional database and complete tenant workflow not established."},
        ],
    }
