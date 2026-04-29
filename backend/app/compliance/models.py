from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomExtract(BaseModel):
    name: str = ""
    area_sqft: Optional[float] = None
    ceiling_ft: Optional[float] = None


class DoorExtract(BaseModel):
    width_in: Optional[float] = None


class StairsExtract(BaseModel):
    rise_in: Optional[float] = None
    tread_in: Optional[float] = None


class EgressWindowExtract(BaseModel):
    area_sqft: Optional[float] = None


class LayoutExtract(BaseModel):
    """Structured metrics inferred from user prompt + CAD DSL (LLM extraction)."""

    model_config = ConfigDict(extra="ignore")

    rooms: List[RoomExtract] = Field(default_factory=list)
    doors_inches: List[DoorExtract] = Field(default_factory=list)
    stairs: Optional[StairsExtract] = None
    egress_windows_sqft: List[EgressWindowExtract] = Field(default_factory=list)
    notes: Optional[str] = None


class ComplianceViolation(BaseModel):
    rule_id: str
    message: str
    suggestion: str


class ComplianceResult(BaseModel):
    jurisdiction_id: str
    jurisdiction_label: str
    score_percent: Optional[float] = None
    status_label: str
    passed_rules: int = 0
    applicable_rules: int = 0
    violations: List[ComplianceViolation] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    disclaimer: str
    layout_extract: Optional[Dict[str, Any]] = None
