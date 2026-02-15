"""LangGraph state definition for the PDF form extraction workflow."""

from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from src.models import (
    EnrichedField,
    OutputField,
    RawField,
    SectionInfo,
    TextElement,
)


def merge_lists(existing: list, new: list) -> list:
    """Reducer that merges lists by extending."""
    return existing + new


def replace_value(existing, new):
    """Reducer that replaces the value."""
    return new


class GraphState(BaseModel):
    """State passed through the LangGraph workflow."""

    # Input
    pdf_path: str = ""

    # Extraction results
    raw_fields: Annotated[list[RawField], merge_lists] = Field(default_factory=list)
    text_elements: Annotated[list[TextElement], merge_lists] = Field(default_factory=list)
    total_pages: int = 0

    # Enrichment tracking
    current_field_index: int = 0
    enriched_fields: Annotated[list[OutputField], merge_lists] = Field(default_factory=list)
    failed_fields: Annotated[list[str], merge_lists] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    # Grouping
    sections: list[SectionInfo] = Field(default_factory=list)

    # Output
    output_json: Optional[str] = None

    # Error tracking
    error: Optional[str] = None
