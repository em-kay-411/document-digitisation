"""Spatial helpers for bbox math and nearby text extraction."""

from __future__ import annotations

import math
import re

from src.models import BBox, TextElement


def euclidean_distance(a: BBox, b: BBox) -> float:
    """Euclidean distance between bbox centers."""
    dx = a.center_x - b.center_x
    dy = a.center_y - b.center_y
    return math.sqrt(dx * dx + dy * dy)


def extract_nearby_text(
    field_bbox: BBox | None,
    field_page: int,
    text_elements: list[TextElement],
    max_distance: float = 150.0,
    max_results: int = 5,
) -> list[str]:
    """Find text elements near a field based on spatial proximity.

    Uses Euclidean distance between bbox centers. Prioritises text to the left
    and above the field (typical label positions).
    """
    if field_bbox is None:
        return []

    candidates: list[tuple[float, str]] = []

    for elem in text_elements:
        if elem.page != field_page or elem.bbox is None:
            continue
        if not elem.text.strip():
            continue

        dist = euclidean_distance(field_bbox, elem.bbox)
        if dist > max_distance:
            continue

        # Boost text that is to the left or above the field (common label positions)
        if elem.bbox.center_x <= field_bbox.center_x or elem.bbox.center_y <= field_bbox.center_y:
            dist *= 0.7

        candidates.append((dist, elem.text.strip()))

    candidates.sort(key=lambda x: x[0])
    return [text for _, text in candidates[:max_results]]


DATE_PATTERNS = re.compile(
    r"(date|dob|birth|mm.?dd|dd.?mm|yyyy|month.?day|day.?month)",
    re.IGNORECASE,
)

SIGNATURE_PATTERNS = re.compile(
    r"(sign(ature)?|sig[_\s]|autograph)",
    re.IGNORECASE,
)


def looks_like_date_field(field_name: str, nearby_text: list[str]) -> bool:
    """Heuristic: does this field look like a date input?"""
    combined = field_name + " " + " ".join(nearby_text)
    return bool(DATE_PATTERNS.search(combined))


def looks_like_signature_field(field_name: str, nearby_text: list[str]) -> bool:
    """Heuristic: does this field look like a signature input?"""
    combined = field_name + " " + " ".join(nearby_text)
    return bool(SIGNATURE_PATTERNS.search(combined))


def slugify(text: str) -> str:
    """Convert text to a slug suitable for IDs."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")
