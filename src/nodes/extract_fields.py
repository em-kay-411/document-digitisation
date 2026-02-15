"""PDF form field extraction using pypdf."""

from __future__ import annotations

import logging
from typing import Any

from pypdf import PdfReader
from pypdf.constants import AnnotationDictionaryAttributes as ADA
from pypdf.generic import ArrayObject, IndirectObject, NameObject

from src.models import BBox, FieldType, RawField
from src.state import GraphState

logger = logging.getLogger(__name__)

# pypdf field type constants (FT values include the slash)
_FT_TEXT = "/Tx"
_FT_BUTTON = "/Btn"
_FT_CHOICE = "/Ch"
_FT_SIGNATURE = "/Sig"

# Field flag bits
_FF_RADIO = 1 << 15  # Bit 16 (0-indexed bit 15) = radio button
_FF_PUSHBUTTON = 1 << 16  # Bit 17 = push button
_FF_COMBO = 1 << 17  # Bit 18 = combo box (dropdown) for choice fields


def _resolve(obj: Any) -> Any:
    """Resolve indirect references."""
    if isinstance(obj, IndirectObject):
        return obj.get_object()
    return obj


def _get_field_flags(field: dict) -> int:
    """Extract field flags (/Ff) value."""
    ff = field.get("/Ff")
    if ff is not None:
        return int(_resolve(ff))
    return 0


def _get_rect_bbox(field: dict) -> BBox | None:
    """Extract bounding box from /Rect annotation."""
    rect = field.get("/Rect")
    if rect is None:
        return None
    rect = _resolve(rect)
    if isinstance(rect, ArrayObject) and len(rect) >= 4:
        coords = [float(_resolve(v)) for v in rect]
        return BBox(l=coords[0], b=coords[1], r=coords[2], t=coords[3])
    return None


def _get_options(field: dict) -> list[str]:
    """Extract /Opt array for choice fields."""
    opt = field.get("/Opt")
    if opt is None:
        return []
    opt = _resolve(opt)
    if not isinstance(opt, ArrayObject):
        return []
    options = []
    for item in opt:
        item = _resolve(item)
        if isinstance(item, ArrayObject) and len(item) >= 2:
            # /Opt can be [[export, display], ...] pairs
            options.append(str(_resolve(item[1])))
        else:
            options.append(str(item))
    return options


def _get_field_type(field: dict, flags: int) -> FieldType:
    """Determine field type from /FT and /Ff flags."""
    ft = field.get("/FT")
    if ft is not None:
        ft = str(_resolve(ft))

    if ft == _FT_TEXT:
        return FieldType.TEXT
    elif ft == _FT_BUTTON:
        if flags & _FF_PUSHBUTTON:
            return FieldType.TEXT  # push buttons treated as text
        if flags & _FF_RADIO:
            return FieldType.RADIO
        return FieldType.CHECKBOX
    elif ft == _FT_CHOICE:
        if flags & _FF_COMBO:
            return FieldType.DROPDOWN
        return FieldType.DROPDOWN  # list boxes also treated as dropdown
    elif ft == _FT_SIGNATURE:
        return FieldType.SIGNATURE

    return FieldType.TEXT  # fallback


def _get_parent_name(field: dict) -> str | None:
    """Get the /T name of the parent for radio button grouping."""
    parent = field.get("/Parent")
    if parent is not None:
        parent = _resolve(parent)
        if isinstance(parent, dict):
            t = parent.get("/T")
            if t is not None:
                return str(_resolve(t))
    return None


def _get_field_name(field: dict) -> str:
    """Extract field name, building the full qualified name."""
    t = field.get("/T")
    if t is not None:
        return str(_resolve(t))
    # Try to build from parent
    parent_name = _get_parent_name(field)
    if parent_name:
        return parent_name
    return "unnamed"


def _extract_fields_from_page(
    reader: PdfReader, page_index: int
) -> list[RawField]:
    """Extract form fields from annotations on a single page."""
    fields = []
    page = reader.pages[page_index]
    annotations = page.get("/Annots")
    if annotations is None:
        return fields

    annotations = _resolve(annotations)
    if not isinstance(annotations, ArrayObject):
        return fields

    for annot_ref in annotations:
        annot = _resolve(annot_ref)
        if not isinstance(annot, dict):
            continue

        subtype = annot.get("/Subtype")
        if subtype is not None and str(_resolve(subtype)) != "/Widget":
            continue

        # Must have /FT or /Parent with /FT
        ft = annot.get("/FT")
        if ft is None:
            parent = annot.get("/Parent")
            if parent is not None:
                parent = _resolve(parent)
                if isinstance(parent, dict):
                    ft = parent.get("/FT")
                    # Merge parent fields we need
                    if "/Ff" not in annot and "/Ff" in parent:
                        annot[NameObject("/Ff")] = parent["/Ff"]
                    if "/Opt" not in annot and "/Opt" in parent:
                        annot[NameObject("/Opt")] = parent["/Opt"]
                    if "/FT" not in annot and ft is not None:
                        annot[NameObject("/FT")] = ft

        if ft is None and annot.get("/FT") is None:
            continue

        flags = _get_field_flags(annot)
        field_type = _get_field_type(annot, flags)
        field_name = _get_field_name(annot)
        bbox = _get_rect_bbox(annot)
        options = _get_options(annot) if field_type in (FieldType.DROPDOWN, FieldType.RADIO) else []

        # Default value
        default_value = None
        v = annot.get("/V")
        if v is not None:
            default_value = str(_resolve(v))

        # Radio group
        radio_group = None
        if field_type == FieldType.RADIO:
            radio_group = _get_parent_name(annot) or field_name

        raw = RawField(
            pdf_field_name=field_name,
            field_type=field_type,
            page=page_index + 1,  # 1-indexed
            bbox=bbox,
            default_value=default_value,
            options=options,
            radio_group=radio_group,
            flags=flags,
        )
        fields.append(raw)

    return fields


def extract_fields_node(state: GraphState) -> dict:
    """LangGraph node: extract all form fields from the PDF."""
    pdf_path = state.pdf_path
    logger.info("Extracting form fields from %s", pdf_path)

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        logger.error("Failed to read PDF: %s", e)
        return {"error": f"Failed to read PDF: {e}"}

    all_fields: list[RawField] = []
    total_pages = len(reader.pages)

    # First try page-level annotations (most reliable for position info)
    for page_idx in range(total_pages):
        page_fields = _extract_fields_from_page(reader, page_idx)
        all_fields.extend(page_fields)

    # If no fields found via annotations, try the AcroForm field tree
    if not all_fields and reader.get_fields():
        form_fields = reader.get_fields()
        for name, field_obj in form_fields.items():
            if not isinstance(field_obj, dict):
                continue
            flags = _get_field_flags(field_obj)
            field_type = _get_field_type(field_obj, flags)
            options = _get_options(field_obj) if field_type in (FieldType.DROPDOWN, FieldType.RADIO) else []

            raw = RawField(
                pdf_field_name=name,
                field_type=field_type,
                page=1,  # AcroForm doesn't give page info easily
                bbox=_get_rect_bbox(field_obj),
                options=options,
                flags=flags,
            )
            all_fields.append(raw)

    logger.info("Extracted %d raw fields across %d pages", len(all_fields), total_pages)

    return {
        "raw_fields": all_fields,
        "total_pages": total_pages,
    }
