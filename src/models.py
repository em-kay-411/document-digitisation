"""Pydantic models for PDF form field extraction and output schema."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    DATE = "date"
    SIGNATURE = "signature"


# --- Raw extraction models ---


class BBox(BaseModel):
    """Bounding box with left, top, right, bottom coordinates."""

    l: float = 0.0
    t: float = 0.0
    r: float = 0.0
    b: float = 0.0

    @property
    def center_x(self) -> float:
        return (self.l + self.r) / 2

    @property
    def center_y(self) -> float:
        return (self.t + self.b) / 2

    @property
    def width(self) -> float:
        return self.r - self.l

    @property
    def height(self) -> float:
        return self.b - self.t


class RawField(BaseModel):
    """A raw form field extracted directly from the PDF."""

    pdf_field_name: str
    field_type: FieldType
    page: int
    bbox: Optional[BBox] = None
    default_value: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    radio_group: Optional[str] = None
    flags: int = 0


class TextElement(BaseModel):
    """A text element extracted from the PDF via PyMuPDF."""

    text: str
    page: int
    bbox: Optional[BBox] = None
    level: int = 0


# --- LLM enrichment models (used with Instructor) ---


class FieldValidation(BaseModel):
    """Validation rules for a form field."""

    max_length: Optional[int] = None
    pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class EnrichedField(BaseModel):
    """LLM-enriched analysis of a single form field."""

    label: str = Field(description="Human-readable label for the field")
    placeholder: Optional[str] = Field(
        None, description="Placeholder text suggestion for text inputs"
    )
    help_text: Optional[str] = Field(
        None, description="Contextual help text for the user"
    )
    required: bool = Field(description="Whether this field is likely required")
    field_type_override: Optional[FieldType] = Field(
        None,
        description="Override field type if LLM detects a more specific type (e.g. date)",
    )
    group: Optional[str] = Field(
        None, description="Logical group name (e.g. 'filing_status' for related checkboxes)"
    )
    validation: Optional[FieldValidation] = None


class SectionAssignment(BaseModel):
    """LLM-determined section assignment for a field."""

    field_id: str
    section_id: str
    section_title: str
    order_in_section: int


class SectionGrouping(BaseModel):
    """LLM output for grouping fields into sections."""

    sections: list[SectionInfo]


class SectionInfo(BaseModel):
    """Information about a form section."""

    section_id: str
    title: str
    order: int
    field_ids: list[str]


# --- Output schema models ---


class OutputField(BaseModel):
    """A single field in the output JSON."""

    field_id: str
    pdf_field_name: str
    type: FieldType
    label: str
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    required: bool = False
    page: int
    order: int
    group: Optional[str] = None
    options: Optional[list[str]] = None
    validation: Optional[FieldValidation] = None


class OutputSection(BaseModel):
    """A section grouping fields in the output JSON."""

    section_id: str
    title: str
    order: int
    fields: list[OutputField]


class OutputMetadata(BaseModel):
    """Metadata about the extraction process."""

    source_pdf: str
    pages: int
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    failed_fields: int = 0


class FormOutput(BaseModel):
    """Top-level output JSON schema."""

    form_id: str
    title: str
    total_fields: int
    sections: list[OutputSection]
    metadata: OutputMetadata
