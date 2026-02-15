"""CLI entry point for PDF form field extraction."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.graph import build_graph
from src.state import GraphState


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDF form fields to UI-ready JSON"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file to extract form fields from",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    if not pdf_path.suffix.lower() == ".pdf":
        print(f"Error: File is not a PDF: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {pdf_path}")

    # Build and run the graph
    graph = build_graph()

    # Use SQLite checkpointer as context manager
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        with SqliteSaver.from_conn_string(":memory:") as checkpointer:
            compiled = graph.compile(checkpointer=checkpointer)
            result = compiled.invoke(
                {"pdf_path": str(pdf_path)},
                config={"configurable": {"thread_id": "main"}},
            )
    except Exception:
        logging.getLogger(__name__).info("Running without checkpointer")
        compiled = graph.compile()
        result = compiled.invoke({"pdf_path": str(pdf_path)})

    # Report results
    if isinstance(result, dict):
        state = GraphState(**result) if not isinstance(result, GraphState) else result
    else:
        state = result

    if state.error:
        print(f"Error: {state.error}", file=sys.stderr)
        sys.exit(1)

    output_path = pdf_path.parent / "output.json"
    enriched_count = len(state.enriched_fields)
    failed_count = len(state.failed_fields)

    print(f"Extracted {enriched_count} fields ({failed_count} failed)")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
