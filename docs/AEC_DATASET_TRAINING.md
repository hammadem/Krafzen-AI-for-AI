# AEC data and model training — 2026-11-27

## Actual assets
- Ten original CC BY 4.0 buildingSMART Certification-datasets IFC samples; four newly collected from pinned tree 5030f652e85d3e679b392fcb38bfa3328d6d9f79. Original Git blob integrity verified. Runtime ingestion checks license, size, source, blob, schema, required entities and SHA-256 deduplication; parses with IfcOpenShell and indexes by discipline. This is reference retrieval, not weight training.
- Existing generated DXF reference suite, separate measured geometry QA.
- 512 original synthetic labelled intent examples, plus 32 nonidentical authored held-out phrases across eight classes. These share domain vocabulary; do not treat as independent production performance. No user files or licensed codebooks included.
- Fitted multinomial Naive Bayes model with Laplace smoothing, log priors and log conditional token probabilities. Local evaluation: 31/32 correct (96.875%); one abstention. Scores are uncalibrated. No automatic tool dispatch, geometry generation or regulatory judgment.

## Reproduce
Run from repository root: `python backend/scripts/train_aec_intent.py --output-dir /tmp/krafzen-aec-training`. The training script checks split uniqueness and synthetic origin, fits parameters on train rows only, evaluates separate test rows, emits model and metrics with dataset digest. Backend CI runs this and uploads evidence. The deployed inference reads the versioned JSON weights, never pickle or downloaded executable models.

## Knowledge collections
Architecture and CAD: synthetic measured DXF references, original intent phrases. BIM: licensed sample geometry, schema and parsed element metadata. Engineering compliance: exact numerical rules and edition-specific links, not scraped standards. Field, reviews and as-built: deterministic project workflows, not trained vision recognition. Keep private customer content separate from all training and public indexes.

## License register
See backend/app/data/aec_dataset_register.json and per-file IFC manifest. CubiCasa5K and FloorPlanCAD are noncommercial. CVC-FP and HouseExpo dataset-specific rights require review; repository code licenses do not necessarily grant rights to underlying data. Swiss Dwellings CC BY 4.0 and individually licensed BIM Open Data are candidates, not collected or processed in this release. No copyrighted codebooks or proprietary customer drawings ingested.

## Product integration and limitations
Chat offers an explicit Suggest AEC task action; the trained classifier abstains on unknown or weak vocabulary, never executes any tool, and no generation credits are consumed. Reference retrieval stays source-backed. Foundation-model fine-tuning, CAD-symbol/OCR vision training, larger independent geometry/architectural datasets and professional evaluation remain outstanding. A GPU service or commercial API is not authorized. Do not market this small classifier as a trained architectural design LLM.
