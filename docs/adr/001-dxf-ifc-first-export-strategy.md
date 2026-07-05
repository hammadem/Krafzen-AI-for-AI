# ADR 001: DXF/IFC-First Export Strategy

**Status:** Accepted (Week 1)  
**Owner:** Kiruthika

## Context

Krafzen already ships DXF, IFC, and DWG generation. The CEO Revit plugin plan targets native Revit long-term. We must not block MVP delivery on `.rvt` authoring.

## Decision

- **Phase 1 (Weeks 1–6):** Harden JSON → DXF/IFC/DWG pipeline; add `revit_package` metadata bundle only.
- **Phase 2 (post Week 6):** Native Revit add-in reads cloud package; optional write-back.

## Consequences

- All exporters consume `ExportModel` (`export_model.py`).
- Marketing must not promise direct `.rvt` export until Phase 2.
- Richard/Fareez geometry work extends `ExportModel`, not parallel schemas.
