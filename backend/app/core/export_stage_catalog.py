"""Frozen export pipeline stage gates — Week 2 architecture (Kiruthika)."""

from app.schemas.export_contracts import (
    ExportStageCatalog,
    ExportStatus,
    PipelineStage,
    StageGateRule,
)

EXPORT_STAGE_CATALOG = ExportStageCatalog(
    stages=[
        StageGateRule(
            stage=PipelineStage.VALIDATION_PRECHECK,
            entry_status=ExportStatus.QUEUED,
            exit_status=ExportStatus.PROCESSING,
            requires_preflight=True,
            description="Validate project/export inputs before worker processing.",
        ),
        StageGateRule(
            stage=PipelineStage.PREPROCESSING,
            entry_status=ExportStatus.PROCESSING,
            exit_status=ExportStatus.PROCESSING,
            description="Normalize source model and attach jurisdiction metadata.",
        ),
        StageGateRule(
            stage=PipelineStage.GEOMETRY_TRANSFORMATION,
            entry_status=ExportStatus.PROCESSING,
            exit_status=ExportStatus.PROCESSING,
            description="Transform canonical ExportModel into target format structures.",
        ),
        StageGateRule(
            stage=PipelineStage.METADATA_INJECTION,
            entry_status=ExportStatus.PROCESSING,
            exit_status=ExportStatus.PROCESSING,
            description="Inject compliance refs, revit_package manifest, and artifact labels.",
        ),
        StageGateRule(
            stage=PipelineStage.EXPORT_GENERATION,
            entry_status=ExportStatus.PROCESSING,
            exit_status=ExportStatus.VALIDATING,
            description="Run DXF/IFC/DWG/revit_package generation (Tazwar worker + existing exporters).",
        ),
        StageGateRule(
            stage=PipelineStage.INTEGRITY_VERIFICATION,
            entry_status=ExportStatus.VALIDATING,
            exit_status=ExportStatus.COMPLETED,
            requires_postflight=True,
            description="Postflight integrity + compliance checks; may route to requires_review.",
        ),
        StageGateRule(
            stage=PipelineStage.ARTIFACT_STORAGE,
            entry_status=ExportStatus.VALIDATING,
            exit_status=ExportStatus.COMPLETED,
            description="Persist artifact via Yehor files row + export_jobs.artifact_file_id.",
        ),
    ],
    max_retries_default=3,
    requires_idempotency_key=True,
)

REVIT_ELEMENT_MAPPINGS = [
    {"krafzen_type": "wall", "revit_category": "Walls", "parameter_map": {"height": "Unconnected Height"}},
    {"krafzen_type": "floor", "revit_category": "Floors", "parameter_map": {"thickness": "Default Thickness"}},
    {"krafzen_type": "door", "revit_category": "Doors", "parameter_map": {"width": "Width", "height": "Height"}},
    {"krafzen_type": "window", "revit_category": "Windows", "parameter_map": {"width": "Width", "height": "Height"}},
    {"krafzen_type": "room", "revit_category": "Rooms", "parameter_map": {"name": "Name", "area": "Area"}},
]
