from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RoomExtract(BaseModel):
    name: str = ""
    area_sqft: float | None = None
    ceiling_ft: float | None = None


class DoorExtract(BaseModel):
    width_in: float | None = None


class StairsExtract(BaseModel):
    rise_in: float | None = None
    tread_in: float | None = None


class EgressWindowExtract(BaseModel):
    area_sqft: float | None = None


class LayoutExtract(BaseModel):
    """Structured metrics inferred from user prompt + CAD DSL (LLM extraction)."""

    model_config = ConfigDict(extra="ignore")

    rooms: list[RoomExtract] = Field(default_factory=list)
    doors_inches: list[DoorExtract] = Field(default_factory=list)
    stairs: StairsExtract | None = None
    egress_windows_sqft: list[EgressWindowExtract] = Field(default_factory=list)
    notes: str | None = None


class ComplianceViolation(BaseModel):
    rule_id: str
    message: str
    suggestion: str


class ComplianceResult(BaseModel):
    jurisdiction_id: str
    jurisdiction_label: str
    score_percent: float | None = None
    status_label: str
    passed_rules: int = 0
    applicable_rules: int = 0
    violations: list[ComplianceViolation] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    disclaimer: str
    layout_extract: dict[str, Any] | None = None
