"""LLM enrichment of form fields using Claude via Instructor."""

from __future__ import annotations

import logging
import time

import anthropic
import instructor

from src.models import EnrichedField, FieldType, OutputField
from src.state import GraphState
from src.utils import (
    extract_nearby_text,
    looks_like_date_field,
    looks_like_signature_field,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-init the Instructor-wrapped Anthropic client."""
    global _client
    if _client is None:
        _client = instructor.from_anthropic(anthropic.Anthropic())
    return _client


def analyze_field_node(state: GraphState) -> dict:
    """LangGraph node: enrich the current field with LLM analysis.

    Processes one field at a time (indexed by current_field_index) to allow
    retry logic via conditional edges.
    """
    idx = state.current_field_index
    raw_fields = state.raw_fields

    if idx >= len(raw_fields):
        # All fields processed
        return {"current_field_index": idx}

    field = raw_fields[idx]
    field_id = f"field_{idx + 1:03d}"

    logger.info(
        "Analyzing field %d/%d: %s", idx + 1, len(raw_fields), field.pdf_field_name
    )

    # Get nearby text for context
    nearby = extract_nearby_text(
        field.bbox, field.page, state.text_elements
    )

    # Apply heuristic type overrides before LLM
    field_type = field.field_type
    if field_type == FieldType.TEXT:
        if looks_like_signature_field(field.pdf_field_name, nearby):
            field_type = FieldType.SIGNATURE
        elif looks_like_date_field(field.pdf_field_name, nearby):
            field_type = FieldType.DATE

    try:
        client = _get_client()
        enriched: EnrichedField = client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze this PDF form field and provide metadata for a UI.\n\n"
                        f"Field name: {field.pdf_field_name}\n"
                        f"Field type: {field_type.value}\n"
                        f"Page: {field.page}\n"
                        f"Options: {field.options if field.options else 'N/A'}\n"
                        f"Default value: {field.default_value or 'N/A'}\n"
                        f"Nearby text (closest first): {nearby}\n\n"
                        f"Provide:\n"
                        f"- A clear human-readable label\n"
                        f"- Placeholder text (for text/date fields)\n"
                        f"- Help text if the context suggests it\n"
                        f"- Whether the field is likely required\n"
                        f"- Validation rules if applicable\n"
                        f"- A group name if this field belongs with related fields\n"
                        f"- Override the field type only if you're confident it should be different"
                    ),
                }
            ],
            response_model=EnrichedField,
        )

        # Build output field
        final_type = enriched.field_type_override or field_type
        output_field = OutputField(
            field_id=field_id,
            pdf_field_name=field.pdf_field_name,
            type=final_type,
            label=enriched.label,
            placeholder=enriched.placeholder,
            help_text=enriched.help_text,
            required=enriched.required,
            page=field.page,
            order=idx + 1,
            group=enriched.group or field.radio_group,
            options=field.options if field.options else None,
            validation=enriched.validation,
        )

        return {
            "enriched_fields": [output_field],
            "current_field_index": idx + 1,
            "retry_count": 0,
        }

    except (anthropic.RateLimitError, anthropic.APITimeoutError) as e:
        logger.warning("Rate limit / timeout on field %d: %s", idx, e)
        # Exponential backoff
        wait = min(2 ** state.retry_count, 30)
        time.sleep(wait)
        return {
            "retry_count": state.retry_count + 1,
            "error": f"Retryable error on field {idx}: {e}",
        }

    except Exception as e:
        logger.error("Failed to analyze field %s: %s", field.pdf_field_name, e)
        # Create a basic output field without LLM enrichment
        fallback = OutputField(
            field_id=field_id,
            pdf_field_name=field.pdf_field_name,
            type=field_type,
            label=field.pdf_field_name,
            required=False,
            page=field.page,
            order=idx + 1,
            group=field.radio_group,
            options=field.options if field.options else None,
        )
        return {
            "enriched_fields": [fallback],
            "failed_fields": [field.pdf_field_name],
            "current_field_index": idx + 1,
            "retry_count": 0,
        }


def should_retry(state: GraphState) -> str:
    """Conditional edge: decide whether to retry, continue, or finish."""
    idx = state.current_field_index

    # If we have a retryable error and haven't exceeded max retries
    if state.retry_count > 0 and state.retry_count <= state.max_retries:
        return "retry"

    # If max retries exceeded, skip field and move on
    if state.retry_count > state.max_retries:
        field = state.raw_fields[idx]
        logger.error("Max retries exceeded for field %s, skipping", field.pdf_field_name)
        return "skip"

    # If more fields to process
    if idx < len(state.raw_fields):
        return "continue"

    # All fields done
    return "done"
