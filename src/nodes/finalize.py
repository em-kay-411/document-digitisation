"""Schema assembly and JSON output."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models import FormOutput, OutputField, OutputMetadata, OutputSection
from src.state import GraphState
from src.utils import slugify

logger = logging.getLogger(__name__)


def finalize_node(state: GraphState) -> dict:
    """LangGraph node: assemble final JSON output and write to disk."""
    pdf_path = Path(state.pdf_path)
    enriched = state.enriched_fields
    sections = state.sections

    # Build a lookup of fields by ID
    field_map: dict[str, OutputField] = {f.field_id: f for f in enriched}

    # Build output sections
    output_sections: list[OutputSection] = []
    for section in sections:
        section_fields = []
        for fid in section.field_ids:
            if fid in field_map:
                section_fields.append(field_map[fid])
            else:
                logger.warning("Field %s in section %s not found", fid, section.section_id)

        # Sort fields within section by page then order
        section_fields.sort(key=lambda f: (f.page, f.order))

        output_sections.append(
            OutputSection(
                section_id=section.section_id,
                title=section.title,
                order=section.order,
                fields=section_fields,
            )
        )

    # Sort sections by order
    output_sections.sort(key=lambda s: s.order)

    # Build form ID from filename
    form_id = slugify(pdf_path.stem)

    # Derive a title from the form ID or first section
    title = pdf_path.stem.replace("_", " ").replace("-", " ").title()

    output = FormOutput(
        form_id=form_id,
        title=title,
        total_fields=len(enriched),
        sections=output_sections,
        metadata=OutputMetadata(
            source_pdf=pdf_path.name,
            pages=state.total_pages,
            failed_fields=len(state.failed_fields),
        ),
    )

    # Write JSON to same directory as the input PDF
    output_path = pdf_path.parent / "output.json"
    output_json = output.model_dump_json(indent=2, exclude_none=True)
    output_path.write_text(output_json)
    logger.info("Output written to %s", output_path)

    return {"output_json": output_json}
