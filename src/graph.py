"""LangGraph workflow builder for PDF form extraction."""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from src.nodes.analyze_field import analyze_field_node, should_retry
from src.nodes.extract_fields import extract_fields_node
from src.nodes.extract_text import extract_text_node
from src.nodes.finalize import finalize_node
from src.nodes.group_fields import group_fields_node
from src.state import GraphState

logger = logging.getLogger(__name__)


def _skip_field_node(state: GraphState) -> dict:
    """Node that skips the current field after max retries and moves on."""
    idx = state.current_field_index
    field = state.raw_fields[idx]
    logger.warning("Skipping field %s after max retries", field.pdf_field_name)
    return {
        "failed_fields": [field.pdf_field_name],
        "current_field_index": idx + 1,
        "retry_count": 0,
    }


def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow.

    Flow:
        START → extract_fields → extract_text → analyze_field ←→ (retry loop)
                                                      ↓
                                                group_fields → finalize → END
    """
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("extract_fields", extract_fields_node)
    graph.add_node("extract_text", extract_text_node)
    graph.add_node("analyze_field", analyze_field_node)
    graph.add_node("skip_field", _skip_field_node)
    graph.add_node("group_fields", group_fields_node)
    graph.add_node("finalize", finalize_node)

    # Linear flow: extract_fields → extract_text → analyze_field
    graph.set_entry_point("extract_fields")
    graph.add_edge("extract_fields", "extract_text")
    graph.add_edge("extract_text", "analyze_field")

    # Conditional edges after analyze_field
    graph.add_conditional_edges(
        "analyze_field",
        should_retry,
        {
            "retry": "analyze_field",       # retry same field
            "skip": "skip_field",           # skip after max retries
            "continue": "analyze_field",    # next field
            "done": "group_fields",         # all fields processed
        },
    )

    # skip_field routes back based on remaining fields
    def _after_skip(state: GraphState) -> str:
        if state.current_field_index < len(state.raw_fields):
            return "analyze_field"
        return "group_fields"

    graph.add_conditional_edges(
        "skip_field",
        _after_skip,
        {
            "analyze_field": "analyze_field",
            "group_fields": "group_fields",
        },
    )

    # group_fields → finalize → END
    graph.add_edge("group_fields", "finalize")
    graph.add_edge("finalize", END)

    return graph


def compile_graph():
    """Compile the graph, optionally with SQLite checkpointing."""
    graph = build_graph()

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        with SqliteSaver.from_conn_string(":memory:") as checkpointer:
            compiled = graph.compile(checkpointer=checkpointer)
            return compiled
    except Exception:
        logger.info("Running without checkpointer")
        return graph.compile()
