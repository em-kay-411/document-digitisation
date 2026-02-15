"""Document text extraction using Docling."""

from __future__ import annotations

import logging

from src.models import BBox, TextElement
from src.state import GraphState

logger = logging.getLogger(__name__)


def extract_text_node(state: GraphState) -> dict:
    """LangGraph node: extract text elements with positions from the PDF using Docling."""
    pdf_path = state.pdf_path
    logger.info("Extracting text elements from %s via Docling", pdf_path)

    text_elements: list[TextElement] = []

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document

        # iterate_items() returns (item, level) tuples
        for item, level in doc.iterate_items():
            text = ""
            if hasattr(item, "text"):
                text = item.text or ""
            elif hasattr(item, "content"):
                text = str(item.content or "")

            if not text.strip():
                continue

            bbox = None
            page = 1

            # Extract provenance / bounding box info
            prov_list = getattr(item, "prov", None)
            if prov_list and len(prov_list) > 0:
                prov = prov_list[0]
                page = getattr(prov, "page_no", 1) or 1

                prov_bbox = getattr(prov, "bbox", None)
                if prov_bbox is not None:
                    # Docling bbox has l, t, r, b attributes
                    bbox = BBox(
                        l=getattr(prov_bbox, "l", 0.0),
                        t=getattr(prov_bbox, "t", 0.0),
                        r=getattr(prov_bbox, "r", 0.0),
                        b=getattr(prov_bbox, "b", 0.0),
                    )

            text_elements.append(
                TextElement(
                    text=text.strip(),
                    page=page,
                    bbox=bbox,
                    level=level,
                )
            )

        logger.info("Extracted %d text elements", len(text_elements))

    except ImportError:
        logger.warning(
            "Docling not available. Falling back to pypdf text extraction."
        )
        text_elements = _fallback_extract_text(pdf_path)
    except Exception as e:
        logger.warning("Docling extraction failed: %s. Falling back to pypdf.", e)
        text_elements = _fallback_extract_text(pdf_path)

    return {"text_elements": text_elements}


def _fallback_extract_text(pdf_path: str) -> list[TextElement]:
    """Simple fallback: extract text per page using pypdf (no bbox info)."""
    from pypdf import PdfReader

    elements: list[TextElement] = []
    reader = PdfReader(pdf_path)
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        for line in text.split("\n"):
            line = line.strip()
            if line:
                elements.append(
                    TextElement(text=line, page=page_idx + 1, bbox=None, level=0)
                )
    return elements
