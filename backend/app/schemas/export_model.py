"""
Canonical ExportModel — internal JSON geometry + metadata for all exporters.

Week 1 draft (Kiruthika). All DXF/IFC/DWG/revit_package outputs consume this shape.
Do not add format-specific top-level fields; nest under `elements` or `metadata`.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    BUILDING = "building"
    LEVEL = "level"
    WALL = "wall"
    FLOOR = "floor"
    DOOR = "door"
    WINDOW = "window"
    ROOM = "room"
    ANNOTATION = "annotation"


class Point3D(BaseModel):
    x: float
    y: float
    z: float = 0.0


class ExportModelMetadata(BaseModel):
    project_id: str
    schema_version: int = Field(default=1, description="ExportModel schema version.")
    jurisdiction_id: str | None = None
    compliance_preset_id: str | None = None
    rule_version: str | None = None
    source_job_id: str | None = None
    units: str = Field(default="imperial", description="imperial | metric")
    extra: dict[str, Any] = Field(default_factory=dict)


class ExportModelElement(BaseModel):
    """
    Universal BIM element. Geometry is abstract (points/lines), not Revit-native.
    """

    krafzen_id: str = Field(..., description="Stable Krafzen element id.")
    revit_id: str | None = Field(default=None, description="Populated after Revit sync (Phase 2).")
    element_type: ElementType
    name: str | None = None
    level_id: str | None = Field(default=None, description="Reference to level krafzen_id.")
    parent_id: str | None = None
    geometry: dict[str, Any] = Field(
        default_factory=dict,
        description="Abstract geometry: points, polylines, bounds, or solid refs.",
    )
    parameters: dict[str, Any] = Field(default_factory=dict)
    relationships: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Adjacency/links, e.g. {'hosted_by': ['wall-1']}.",
    )


class ExportModel(BaseModel):
    """Single canonical model snapshot passed to exporters and compliance checks."""

    metadata: ExportModelMetadata
    elements: list[ExportModelElement] = Field(default_factory=list)


def example_export_model() -> ExportModel:
    """Template instance for GET /contracts/export-model."""
    return ExportModel(
        metadata=ExportModelMetadata(
            project_id="example-project-id",
            jurisdiction_id="US_IRC_BASELINE",
            compliance_preset_id="us-irc-baseline-v1",
            rule_version="us_irc_baseline@1",
        ),
        elements=[
            ExportModelElement(
                krafzen_id="level-1",
                element_type=ElementType.LEVEL,
                name="Level 1",
                geometry={"elevation": 0.0},
            ),
            ExportModelElement(
                krafzen_id="room-1",
                element_type=ElementType.ROOM,
                name="Bedroom 1",
                level_id="level-1",
                geometry={"boundary": [[0, 0], [12, 0], [12, 10], [0, 10]]},
                parameters={"area_sqft": 120},
            ),
        ],
    )
