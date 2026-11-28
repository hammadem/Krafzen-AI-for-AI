# US data residency — evidence assessment (2026-11-27)

The connected Supabase project was verified in AWS us-east-1; frontend and API Render services in Virginia. Provider project location and observed configuration do not establish exclusive US processing.

| Path | Evidence / decision |
|---|---|
| Primary database, Auth, storage origin | US provider project region; https://supabase.com/docs/guides/platform/regions |
| Storage delivery/CDN | Unverified US-only boundary. Supabase documents global CDN caching: https://supabase.com/docs/guides/storage/cdn/fundamentals ; https://supabase.com/legal/privacy-resources/data-residency-and-transfers-faq |
| Render service execution and stored service logs | Virginia service region and provider documented regional log storage: https://render.com/docs/regions ; https://render.com/docs/logging |
| External logs, control plane, support, third-party transfers | Outstanding contractual and configuration evidence |
| Backups | Need documented approved US database and object backup targets, tested recovery, retention; https://supabase.com/docs/guides/platform/backups |
| Native DWG processing | Actual synthetic round-trip verified on existing Virginia backend. No claim of general conversion fidelity. |
| Local AEC intent and browser symbol inference | No external AI provider required for these bounded advisory features; client device location is not asserted. |
| External LLM, mail, billing, OAuth | No exclusive US processing guarantee established. Sovereign features remain gated. |
| Dedicated scanner | Not provisioned; ClamAV recommends 3–4 GiB RAM, current backend 512 MiB: https://docs.clamav.net/Introduction.html |
| Revit desktop | User device, licensing and region not independently established; native export must be verified on authorized Windows/Revit host. |
| Sovereign tenant data, backups, workers | Dedicated regional pipeline and complete isolation not verified. |

Do not enable a US-only certification or region cutover based on this assessment. A real release requires provider contracts, transfer controls, private non-global storage path, configured approved compute/scanner, independent verification and recorded recovery tests. No customer data was migrated or transferred to evaluate these paths.
