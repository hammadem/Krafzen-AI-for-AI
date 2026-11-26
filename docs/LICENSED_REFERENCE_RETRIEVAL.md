# Licensed reference retrieval (initial implementation)

- Source: buildingSMART International certification IFC examples, CC BY 4.0, copied without modification.
- Dataset register: backend/tests/fixtures/aec_reference/reference_manifest.json. GET /api/v1/chat/reference-register exposes verified format, version, source URL, attribution, hash, license and processing status.
- Ingestion: bound the manifest; reject unexpected license, path, size or Git blob; deduplicate by SHA-256; parse actual IFC entities; extract product class counts, classify by discipline, construct a lexical index.
- Query: in a paid workspace, type /reference IFC wall opening window in chat. The server returns relevant records, source URLs and license/attribution and persists the question/answer in the authenticated session. No external model request or AI-generation credit consumption occurs.
- Scope: initial deterministic retrieval over approved IFC examples, not a complete technical knowledge base or weight training. Customer files are not indexed. Queries must contain a matching technical term: generic IFC/model/project vocabulary and boilerplate disclaimers are not indexed as evidence. Unknown questions return no matching evidence. Other third-party material requires documented rights review before ingestion.
- Evaluation: original blob/hash, source entity counts, license enforcement, tamper rejection, relevance and isolated account/session tests.
