"""Document text extraction using PyMuPDF."""

from __future__ import annotations

import logging

import fitz

from src.models import BBox, TextElement
from src.state import GraphState

logger = logging.getLogger(__name__)


def extract_text_node(state: GraphState) -> dict:
    """LangGraph node: extract text elements with positions from the PDF using PyMuPDF."""
    pdf_path = state.pdf_path
    logger.info("Extracting text elements from %s via PyMuPDF", pdf_path)

    text_elements: list[TextElement] = []

    doc = fitz.open(pdf_path)
    for page_idx, page in enumerate(doc):
        page_height = page.rect.height
        data = page.get_text("dict")

        # Collect all font sizes on the page to infer heading levels
        font_sizes: list[float] = []
        for block in data["blocks"]:
            if block["type"] != 0:  # skip image blocks
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["text"].strip():
                        font_sizes.append(span["size"])

        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    x0, y0, x1, y1 = span["bbox"]

                    # Convert from top-left origin (PyMuPDF) to bottom-left origin
                    # to match extract_fields.py coordinate system
                    bbox = BBox(
                        l=x0,
                        t=page_height - y0,
                        r=x1,
                        b=page_height - y1,
                    )

                    level = _infer_level(span["size"], font_sizes)

                    text_elements.append(
                        TextElement(
                            text=text,
                            page=page_idx + 1,
                            bbox=bbox,
                            level=level,
                        )
                    )

    doc.close()
    logger.info("Extracted %d text elements", len(text_elements))
    return {"text_elements": text_elements}


def _infer_level(size: float, all_sizes: list[float]) -> int:
    """Infer a heading level from font size. Larger fonts get lower level numbers."""
    if not all_sizes:
        return 0
    max_size = max(all_sizes)
    min_size = min(all_sizes)
    if max_size == min_size:
        return 0
    # Normalize: largest font → level 0, smallest → level 5
    ratio = (max_size - size) / (max_size - min_size)
    return min(int(ratio * 5), 5)
