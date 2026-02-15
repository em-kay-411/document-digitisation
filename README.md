# Document Digitisation

A PDF form field extraction and enrichment system that converts static PDF forms into structured, UI-ready JSON using **LangGraph**, **Claude AI**, and **PyMuPDF**. It extracts form fields, enriches them with intelligent metadata via an LLM, and outputs a complete JSON schema suitable for rendering dynamic web forms.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Pipeline Walkthrough](#pipeline-walkthrough)
  - [Step 1: Extract Fields](#step-1-extract-fields-extract_fieldspy)
  - [Step 2: Extract Text](#step-2-extract-text-extract_textpy)
  - [Step 3: Analyze Fields](#step-3-analyze-fields-analyze_fieldpy)
  - [Step 4: Group Fields](#step-4-group-fields-group_fieldspy)
  - [Step 5: Finalize Output](#step-5-finalize-output-finalizepy)
- [Data Models](#data-models)
- [Graph State](#graph-state)
- [Utility Functions](#utility-functions)
- [Coordinate Systems](#coordinate-systems)
- [Rendering](#rendering)
- [Test Form Generator](#test-form-generator)
- [Dependencies](#dependencies)

---

## Architecture Overview

```
                         LangGraph Workflow
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   START                                                          │
│     │                                                            │
│     ▼                                                            │
│   extract_fields ──► extract_text ──► analyze_field ◄──┐         │
│   (pypdf)            (PyMuPDF)        (Claude LLM)     │         │
│                                           │            │         │
│                                      should_retry?     │         │
│                                       /    |    \      │         │
│                                 retry/  skip  continue │         │
│                                   │      │       │     │         │
│                                   └──────┤       └─────┘         │
│                                          │    (next field)       │
│                                          ▼                       │
│                                     group_fields                 │
│                                          │                       │
│                                          ▼                       │
│                                      finalize ──► output.json    │
│                                          │                       │
│                                         END                      │
└──────────────────────────────────────────────────────────────────┘
```

The system processes one PDF through six nodes. Fields are extracted from the PDF's annotation layer (pypdf), text with bounding boxes is extracted separately (PyMuPDF), then each field is enriched one at a time by Claude using nearby text as spatial context. Fields are grouped into sections by page and serialized to JSON.

---

## Project Structure

```
document-digitisation/
├── src/
│   ├── __init__.py
│   ├── models.py                # Pydantic data models
│   ├── state.py                 # LangGraph state definition
│   ├── utils.py                 # Spatial helpers, pattern matching
│   ├── graph.py                 # LangGraph workflow builder
│   ├── main.py                  # CLI entry point
│   └── nodes/
│       ├── __init__.py
│       ├── extract_fields.py    # PDF form field extraction (pypdf)
│       ├── extract_text.py      # Text + bbox extraction (PyMuPDF)
│       ├── analyze_field.py     # LLM enrichment (Claude + Instructor)
│       ├── group_fields.py      # Page-based section grouping
│       └── finalize.py          # JSON assembly and output
├── pyproject.toml               # Project config and dependencies
├── generate_test_form.py        # Generates a sample 11-page PDF
├── render.js                    # Converts output.json → form.html
├── test_form.pdf                # Sample PDF (generated)
├── output.json                  # Extraction result
└── form.html                    # Rendered HTML form
```

---

## Installation

```bash
# Clone and install
git clone <repo-url>
cd document-digitisation
pip install -e .

# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

Requires Python >= 3.10.

---

## Usage

### Extract form fields from a PDF

```bash
# Via installed script
extract-form path/to/form.pdf

# Or as a module
python -m src.main path/to/form.pdf

# With debug logging
extract-form path/to/form.pdf -v
```

Output is written to `output.json` in the same directory as the input PDF.

### Render to HTML

```bash
node render.js output.json
# Produces: form.html
```

### Generate a test PDF

```bash
python generate_test_form.py
# Produces: test_form.pdf (11 pages, 199 fields)
```

---

## Pipeline Walkthrough

### Step 1: Extract Fields (`extract_fields.py`)

**Node function:** `extract_fields_node(state) -> dict`

Opens the PDF with pypdf and extracts every interactive form field (text inputs, checkboxes, radio buttons, dropdowns, signatures) from the page annotation layer.

**How it works:**

1. Iterates through each page's `/Annots` array looking for `/Widget` annotations (form fields).
2. For each widget, resolves indirect object references and reads:
   - `/FT` (field type): `/Tx` = text, `/Btn` = button, `/Ch` = choice, `/Sig` = signature
   - `/Ff` (field flags): bit 16 = radio, bit 17 = push button, bit 18 = combo/dropdown
   - `/Rect` (bounding box): `[left, bottom, right, top]` in PDF coordinate space
   - `/T` (field name): may include parent name for hierarchical fields
   - `/Opt` (options): for dropdowns and radio buttons
   - `/V` or `/DV` (default value)
3. Handles hierarchical fields — radio buttons share a parent that holds the group name and field type.
4. Falls back to the global AcroForm field tree if no page-level annotations are found.

**Key helper functions:**

| Function | Purpose |
|----------|---------|
| `_resolve(obj)` | Dereferences pypdf `IndirectObject` to get the actual value |
| `_get_field_type(field, flags)` | Maps `/FT` + flag bits to a `FieldType` enum |
| `_get_rect_bbox(field)` | Extracts `/Rect` as a `BBox(l, t, r, b)` |
| `_get_options(field)` | Reads `/Opt` array for choice fields |
| `_get_field_name(field)` | Builds the full qualified name including parent `/T` |
| `_get_parent_name(field)` | Gets the parent field name (used for radio groups) |
| `_extract_fields_from_page(reader, page_index)` | Extracts all fields from a single page |

**Returns:** `{"raw_fields": [RawField, ...], "total_pages": int}`

---

### Step 2: Extract Text (`extract_text.py`)

**Node function:** `extract_text_node(state) -> dict`

Extracts every visible text element from the PDF along with its position and font size, using PyMuPDF. This text is used later to give the LLM spatial context about each field (e.g., finding the label "First Name" near a text input).

**How it works:**

1. Opens the PDF with `fitz.open(pdf_path)`.
2. For each page, calls `page.get_text("dict")` which returns a structured dictionary:
   ```
   {"blocks": [{"type": 0, "lines": [{"spans": [{"text": "...", "bbox": (x0,y0,x1,y1), "size": 12.0, ...}]}]}]}
   ```
   - `type: 0` = text block, `type: 1` = image block (skipped)
   - Each span contains: `text`, `bbox`, `size` (font size), `font` (font name)
3. Collects all font sizes on the page, then infers heading levels from font size (see `_infer_level`).
4. Converts PyMuPDF coordinates (top-left origin) to bottom-left origin to match the coordinate system used by `extract_fields.py`. See [Coordinate Systems](#coordinate-systems).

**Key helper function:**

- `_infer_level(size, all_sizes) -> int`: Maps font size to a heading level 0–5. The largest font on the page gets level 0 (most prominent heading), the smallest gets level 5. The formula normalizes linearly: `ratio = (max_size - size) / (max_size - min_size)`, then `level = min(int(ratio * 5), 5)`.

**Returns:** `{"text_elements": [TextElement, ...]}`

---

### Step 3: Analyze Fields (`analyze_field.py`)

**Node function:** `analyze_field_node(state) -> dict`

The core enrichment step. Processes **one field per invocation** (LangGraph loops back to this node until all fields are done). For each field:

1. **Finds nearby text** using `extract_nearby_text()` — retrieves the 5 closest text elements within 150 PDF units, with a spatial priority boost for text to the left or above (typical label positions).

2. **Applies heuristics** before calling the LLM:
   - `looks_like_date_field()` checks field name and nearby text against date patterns (e.g., "dob", "mm/dd/yyyy")
   - `looks_like_signature_field()` checks for signature patterns (e.g., "sign", "signature")
   - If a text field matches, its type is overridden to `DATE` or `SIGNATURE`

3. **Calls Claude** via Instructor for structured output:
   - Model: `claude-sonnet-4-5-20250929`
   - Prompt includes: field name, type, page, options, default value, nearby text
   - Response model: `EnrichedField` (Pydantic) — Instructor ensures the LLM returns valid structured data
   - Extracts: `label`, `placeholder`, `help_text`, `required`, `validation`, `group`, `field_type_override`

4. **Combines** the raw `RawField` with the `EnrichedField` into an `OutputField`, assigning a sequential `field_id` like `"field_001"`.

**Retry logic** (via `should_retry` conditional edge):

| Condition | Action |
|-----------|--------|
| API rate limit or timeout | Sleep with exponential backoff, retry (up to 3 times) |
| Max retries exceeded | Skip field, add to `failed_fields`, move to next |
| Success, more fields remain | Loop back to `analyze_field` for next field |
| All fields processed | Proceed to `group_fields` |

**Client initialization:** `_get_client()` lazily creates an Instructor-wrapped Anthropic client on first call, avoiding API key loading at import time.

**Returns on success:** `{"enriched_fields": [OutputField], "current_field_index": idx+1, "retry_count": 0}`

---

### Step 4: Group Fields (`group_fields.py`)

**Node function:** `group_fields_node(state) -> dict`

Groups enriched fields into sections. Currently uses a simple page-based grouping strategy:

1. Groups all field IDs by their `page` number.
2. Creates a `SectionInfo` for each page with `section_id = "page_1"`, `title = "Page 1"`, etc.
3. Sections are ordered by page number.

This could be extended to use LLM-based semantic grouping (e.g., grouping "First Name", "Last Name", "SSN" into a "Personal Information" section regardless of page).

**Returns:** `{"sections": [SectionInfo, ...]}`

---

### Step 5: Finalize Output (`finalize.py`)

**Node function:** `finalize_node(state) -> dict`

Assembles the final JSON output:

1. Creates a lookup map from `field_id` to `OutputField`.
2. Builds `OutputSection` objects by mapping each section's `field_ids` to actual `OutputField` instances.
3. Sorts fields within each section by page then order; sorts sections by order.
4. Derives `form_id` from the PDF filename via `slugify()` (e.g., `"test_form"`).
5. Derives `title` by replacing underscores/hyphens with spaces and title-casing (e.g., `"Test Form"`).
6. Creates `FormOutput` with metadata (source PDF name, page count, timestamp, failed field count).
7. Serializes to JSON with `model_dump_json(indent=2, exclude_none=True)`.
8. Writes to `output.json` in the same directory as the input PDF.

**Returns:** `{"output_json": json_string}`

---

## Data Models

All models are defined in `src/models.py` using Pydantic.

### Raw Extraction Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `BBox` | Bounding box coordinates | `l`, `t`, `r`, `b` (left, top, right, bottom). Properties: `center_x`, `center_y`, `width`, `height` |
| `RawField` | Form field from PDF | `pdf_field_name`, `field_type`, `page`, `bbox`, `default_value`, `options`, `radio_group`, `flags` |
| `TextElement` | Text from PDF | `text`, `page`, `bbox`, `level` (heading level 0–5) |
| `FieldType` | Enum | `TEXT`, `CHECKBOX`, `RADIO`, `DROPDOWN`, `DATE`, `SIGNATURE` |

### LLM Enrichment Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `EnrichedField` | Claude's analysis of a field | `label`, `placeholder`, `help_text`, `required`, `field_type_override`, `group`, `validation` |
| `FieldValidation` | Validation rules | `max_length`, `pattern` (regex), `min_value`, `max_value` |

### Output Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `OutputField` | Final field in JSON | Combines raw + enriched: `field_id`, `pdf_field_name`, `type`, `label`, `placeholder`, `help_text`, `required`, `page`, `order`, `group`, `options`, `validation` |
| `OutputSection` | Section grouping | `section_id`, `title`, `order`, `fields: list[OutputField]` |
| `FormOutput` | Top-level output | `form_id`, `title`, `total_fields`, `sections`, `metadata` |
| `OutputMetadata` | Extraction metadata | `source_pdf`, `pages`, `extracted_at`, `failed_fields` |

---

## Graph State

Defined in `src/state.py`. The `GraphState` is a single Pydantic model passed through every node in the workflow.

```python
class GraphState(BaseModel):
    pdf_path: str                    # Input PDF path
    raw_fields: list[RawField]       # From extract_fields
    text_elements: list[TextElement] # From extract_text
    total_pages: int                 # Page count
    current_field_index: int         # Loop counter for analyze_field
    enriched_fields: list[OutputField] # Accumulated results
    failed_fields: list[str]         # Fields that couldn't be enriched
    retry_count: int                 # Current retry attempt
    max_retries: int                 # Default 3
    sections: list[SectionInfo]      # From group_fields
    output_json: Optional[str]       # Final JSON string
    error: Optional[str]             # Error message if any
```

Fields annotated with `Annotated[list[T], merge_lists]` accumulate values across node executions (LangGraph reducer pattern). This means when a node returns `{"enriched_fields": [field]}`, it gets **appended** to the existing list rather than replacing it.

---

## Utility Functions

Defined in `src/utils.py`.

### `extract_nearby_text(field_bbox, field_page, text_elements, max_distance=150.0, max_results=5)`

The spatial intelligence behind field enrichment. Finds text elements near a form field to give the LLM context.

1. Filters text elements to the same page.
2. Calculates Euclidean distance between bbox centers.
3. **Spatial priority boost**: Text to the left of or above the field gets its distance multiplied by 0.7 (30% closer). This reflects the common convention that labels appear to the left of or above their associated fields.
4. Filters to elements within `max_distance` (default 150 PDF units).
5. Returns up to `max_results` (default 5) closest text strings, sorted by distance.

### `euclidean_distance(a, b)`

Standard distance between two bounding box centers: `sqrt((a.center_x - b.center_x)^2 + (a.center_y - b.center_y)^2)`.

### `looks_like_date_field(field_name, nearby_text)` / `looks_like_signature_field(field_name, nearby_text)`

Regex-based heuristics that check the field name and nearby text against known patterns. Used as a fast pre-check before the LLM call to override field types.

### `slugify(text)`

Converts text to a lowercase slug with underscores. `"First Name"` becomes `"first_name"`.

---

## Coordinate Systems

Two different coordinate systems are used and must be aligned:

| Source | Origin | Y-axis | Used by |
|--------|--------|--------|---------|
| PDF spec / pypdf | Bottom-left | Increases upward | `extract_fields.py` |
| PyMuPDF | Top-left | Increases downward | `extract_text.py` (raw) |

`extract_fields.py` reads the PDF `/Rect` array `[left, bottom, right, top]` and maps it to `BBox(l=left, t=top, r=right, b=bottom)`. In this system, `t > b` because `top` is a higher Y value than `bottom`.

`extract_text.py` receives PyMuPDF bounding boxes as `(x0, y0, x1, y1)` in top-left origin. It converts to bottom-left origin using:

```python
bbox = BBox(
    l=x0,
    t=page_height - y0,   # top in bottom-left coords
    r=x1,
    b=page_height - y1,   # bottom in bottom-left coords
)
```

This keeps both text and field bounding boxes in the same coordinate space, so `extract_nearby_text()` can compute meaningful distances.

---

## Rendering

`render.js` converts `output.json` into a standalone `form.html` with:

- **Sidebar navigation** with section links and scroll-spy (highlights active section using `IntersectionObserver`)
- **Responsive layout** that works on mobile
- **Field type rendering**:
  - `text` → `<input type="text">` with optional `maxlength` and `pattern`
  - `date` → `<input type="date">`
  - `checkbox` → checkbox with label
  - `radio` → radio group with options
  - `dropdown` → `<select>` with `<option>` elements
  - `signature` → text input styled with a cursive font and dashed border
- **Help text** displayed below each field
- **Required field** indicators

```bash
node render.js output.json
open form.html
```

---

## Test Form Generator

`generate_test_form.py` produces a realistic 11-page "Small Business Loan Application" PDF with 199 fields using ReportLab. It includes:

- Personal information (name, SSN, DOB)
- Business details (name, EIN, address, revenue)
- Financial information (assets, liabilities)
- Loan details (amount, purpose, term)
- Collateral and references
- Signatures and certifications

The `FormBuilder` class provides methods for creating each field type (`text_field`, `checkbox`, `radio_group`, `dropdown`, `date_field`, `signature_field`) with proper PDF annotations and labels.

```bash
pip install reportlab
python generate_test_form.py
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | >= 0.2.0 | Workflow orchestration with state management |
| `langgraph-checkpoint-sqlite` | >= 2.0.0 | Optional state checkpointing (in-memory SQLite) |
| `langchain-core` | >= 0.3.0 | LangChain primitives |
| `anthropic` | >= 0.40.0 | Claude API client |
| `instructor` | >= 1.7.0 | Structured LLM outputs via Pydantic |
| `pypdf` | >= 4.0.0 | PDF form field extraction |
| `PyMuPDF` | >= 1.24.0 | Text extraction with bounding boxes |
| `pydantic` | >= 2.0.0 | Data validation and serialization |

**Optional (for tooling):**

| Package | Purpose |
|---------|---------|
| `reportlab` | Generating the test PDF (`generate_test_form.py`) |
| `node` | Rendering HTML form (`render.js`) |
