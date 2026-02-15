"""Section grouping by page."""

from __future__ import annotations

import logging
from collections import defaultdict

from src.models import SectionInfo
from src.state import GraphState

logger = logging.getLogger(__name__)


def group_fields_node(state: GraphState) -> dict:
    """LangGraph node: group enriched fields by page number."""
    enriched = state.enriched_fields

    if not enriched:
        logger.warning("No enriched fields to group")
        return {"sections": []}

    pages: dict[int, list[str]] = defaultdict(list)
    for f in enriched:
        pages[f.page].append(f.field_id)

    sections = [
        SectionInfo(
            section_id=f"page_{page}",
            title=f"Page {page}",
            order=page,
            field_ids=field_ids,
        )
        for page, field_ids in sorted(pages.items())
    ]

    logger.info("Grouped %d fields into %d page sections", len(enriched), len(sections))
    return {"sections": sections}
