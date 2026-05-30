# PROMPT: Generate Paperwork — Video Storyboard Script (Markdown)

---

## YOUR ROLE

You are a professional presentation scriptwriter and storyboard director specialising in **enterprise tech product videos**. You are being asked to generate a **complete, detailed, word-for-word video storyboard script** for a 4-minute product explainer video.

The output must be a **single, well-structured Markdown file** that can be handed directly to a PowerPoint generator to build the slide deck. Every slide must be fully described with enough detail that no further clarification is needed.

---

## CONTEXT: THE PRODUCT

**Product name:** Paperwork — Intelligent Document Tagging & Digitization

**What it does:** Paperwork solves two major problems in financial fund document workflows:

### Problem 1 — Document Tagging
- Subscription documents for financial funds are 200–700 pages long with ~300 editable fields (textboxes, checkboxes, radio groups).
- Every editable field must be given a specific tag name (e.g. `txt_subscriberName`) so that data can be filled programmatically from a database, and so that all PDFs across a fund are consistently tagged.
- Tag names must be consistent across all documents for the same fund — so a field asking for the subscriber's name always has the same tag regardless of where it appears or what surrounds it.
- Because the surrounding text (context) changes in every PDF, tagging requires human judgement — a person must read around every field to understand what it is.
- Today this is done manually in Adobe Acrobat Pro, field by field, for all ~300 fields per document. It takes **5–6 days per document**.
- After tagging, the document must be tested — all 300 fields checked for correctness. Errors mean re-tagging and re-testing.
- This creates a **bottleneck on fund launches**: no document, no fund.

### Problem 2 — Document Filling
- After a document is tagged, bankers must fill the non-programmatic fields and review the whole document before sending to clients.
- With 300 fields spread across 200+ pages, this is a painful scrolling experience.
- A navigation panel was built to jump between fields — but the UX is still fragmented: no descriptions, no grouping, no context, no logical sections.
- This costs hours per document review cycle.

---

## CONTEXT: THE SOLUTIONS

> **Note:** The detailed technical implementation of both solutions is described in the two attached markdown files. Use them as the authoritative technical reference for all solution slides. Do not invent technical details — use what is in those files.

### Solution 1 — AI Tagging Tool
- Accepts a PDF as input, runs it through a hybrid AI prediction pipeline, and applies tags to all fields automatically.
- A **Conflict Resolver screen** appears after tagging — flagged low-confidence fields are shown with the AI's top tag options. User picks or types a custom tag. Cannot proceed without resolving all conflicts.
- A **Tag Editing screen** follows — a custom-built PDF viewer (left) with a fields panel (right). Clicking a field in the panel scrolls to it in the PDF. Right-click on any field shows: Modify Tag / Modify Group / Modify Value (radio/checkbox only). Text fields only have Modify Tag.
- On save, a **Rules Excel** is auto-generated — all field enable/disable logic based on other field values. Used in DocuSign and in the custom viewer.
- Tagging time drops from **5–6 days → 15–30 minutes**.

### Solution 2 — Document Digitization
- Accepts a PDF and runs it through a LangGraph pipeline to produce a **Form JSON** — a structured representation of all fields with labels, placeholders, help text, required flags, groups, and options.
- The **pdf-forms web component** takes three inputs: PDF (base64), Rules Excel, Form JSON — and renders a clean HTML form UI (like Google Forms) with sections, labels, and help text.
- The component is **plug-and-play**: any framework, lightweight, zero lock-in.
- Values filled in the form **write back to the original PDF** on save.
- A **built-in testing UI** lets you test the rendered form before shipping it anywhere.

---

## CONTEXT: THE IMPACT

- Tagging time: **7 days → 15–30 minutes**
- Effort reduction: **97%**
- 300 fields now navigated in a **clean, sectioned form UI** — minutes instead of hours
- Fund launches no longer blocked by document bottlenecks
- Same team, redirected to higher-value work
- Plug-and-play integration — works in any existing stack

---

## THE VIDEO STRUCTURE

The video is exactly **4 minutes (240 seconds)** long. It has 7 sections:

| Section | Time Range | Duration | Slide Count |
|---|---|---|---|
| INTRO | 0:00–0:20 | 20s | 8 slides |
| PROBLEM: TAGGING | 0:20–1:15 | 55s | 18 slides |
| PROBLEM: FILLING | 1:15–1:45 | 30s | 9 slides |
| SOLUTION: TAGGING | 1:45–2:45 | 60s | 19 slides |
| SOLUTION: DIGITIZE | 2:45–3:25 | 40s | 13 slides |
| IMPACT | 3:25–3:50 | 25s | 8 slides |
| CLOSE | 3:50–4:00 | 10s | 3 slides |
| **TOTAL** | **0:00–4:00** | **240s** | **78 slides** |

The slide durations within each section are already specified in the **Slide-by-Slide Script** section below. You must respect them exactly — the total must equal 240 seconds.

---

## DESIGN LANGUAGE

Apply these consistently in all `[VISUAL]` descriptions:

| Element | Value |
|---|---|
| Background | Near-black (`#0D0D0D`) or section-specific dark variant |
| Intro / Solution-Tag accent | Electric blue `#00C2FF` |
| Problem accent | Red `#FF3B30` |
| Solution-Dig accent | Green `#34C759` |
| Impact accent | Gold `#FFD60A` |
| Stat slam font size | 96–120 pt, bold |
| Section heading size | 48–64 pt |
| Slide heading size | 32–40 pt |
| Subtext | 20–28 pt |
| Caption/label | 14–18 pt |
| Font family | Arial / Montserrat / Inter |

**Tone:** Cinematic, fast-cut, confident. Problem section feels urgent and painful. Solution section feels intelligent and calm. Impact section feels like a payoff.

---

## OUTPUT FORMAT

Generate the storyboard as a Markdown file structured exactly as follows. Every slide must use this template:

```
---

### Slide [NUMBER] — [SECTION]
**Timestamp:** [START]–[END] &nbsp;|&nbsp; **Duration:** [X]s

#### 🖥 On Screen
[Describe every element visible on the slide — headline text, body text, layout, visual elements (diagrams, mockups, icons, code blocks, split screens), colour accents, overlays. Be specific enough that a designer can build this slide without asking any questions.]

#### 🎙 Voiceover
> [Word-for-word narration. Complete sentences. Natural speech rhythm. No bullet points here — this is spoken aloud.]

#### ✨ Animations
[List each element and its entrance animation. Format: Element name → Animation type, speed, trigger (On Click / After Previous / With Previous).]

#### ➡ Transition to Next
[Transition name and speed — e.g. Cut (0s), Fade (0.3s), Morph (0.5s), Push Right (0.3s), Zoom (0.4s)]

#### 📝 Director's Notes
[Style intent, emphasis cues, what to hold, what not to rush, screenshot/mockup guidance, tone notes.]

---
```

---

## NARRATIVE BEATS TO HIT

Follow this arc — every section has a mandatory narrative beat:

### INTRO (0:00–0:20)
- Open with THREE number slams: **7 DAYS** → **300 FIELDS** → **700 PAGES** using Morph transitions (2s each)
- Brief context line: "One document. Every fund. Every time."
- Pivot with electric blue glow: "We changed all of it."
- Brand reveal: Paperwork logo + tagline
- Road map card: "Two problems. Both solved."

### PROBLEM: TAGGING (0:20–1:15)
- Chapter card: "THE PROBLEM — Part 1: Document Tagging"
- Explain what a tag IS with a simple diagram (tag label above a field)
- Show the density: full-screen PDF mockup with all fields highlighted
- Show the three field types (textbox, checkbox, radio) colour-coded
- Show WHY context matters: two PDFs side by side, same field, different surroundings
- Show the code dependency: programmatic filling relies on consistent tag names
- Directional context explanation: why surrounding text differs per field type
- Radio button complexity: export values, group assignment, ordering
- Adobe Acrobat Pro screen: manual entry, field by field
- Counter animation: Field 1 → 12 → 47 → 134 → 300 (jarring cuts)
- 5–6 day stat card (red)
- Testing phase pain: after tagging, must verify all 300 fields
- Fund launch timeline: long red bar representing the wait
- Document queue: 12 more waiting behind the one being tagged
- Business cost: delayed launches, wasted specialist time, revenue held back
- Bridge: "What if tagging was automatic?" with blank right side (anticipation)

### PROBLEM: FILLING (1:15–1:45)
- Chapter card: "PROBLEM 2 — Document Filling"
- Scrolling PDF animation (page counter ticking)
- Navigation panel demo + why it's still broken
- Extra pain: no descriptions, no grouping, no context
- Three pain bullets: no grouping / broken flow / hours per review
- Red overlay + opportunity cost framing
- HOURS stat card with multiplication formula
- Left/right comparison: what team WANTS to do vs what process FORCES
- "Until now." pivot with blue glow + full section bridge

### SOLUTION: TAGGING (1:45–2:45)
- Chapter card: "THE SOLUTION — Part 1: AI-Powered Tagging Tool"
- Four-line promise: Upload PDF → AI tags it → Review conflicts → Done
- Knowledge stores (from attached tech doc): Raw context map / Lemmatized map / FAISS vector index + supporting stores
- Learning over time: system gets smarter with every PDF
- Directional context extraction (field-type aware)
- Prediction pipeline — build one node per slide (5 nodes): Exact Match → Fuzzy Raw → Fuzzy Lemmatized → Vector Search → LLM (last resort)
- Full pipeline callout: 97% deterministic, LLM only for edge cases
- Confidence scoring: 95% → auto assign, 48% → conflict flagged
- Conflict Resolver UI mockup
- Tag Editing screen mockup (PDF viewer + fields panel)
- Right-click context menu: Modify Tag / Modify Group / Modify Value
- Auto-save + Rules Excel generation
- "Done in one session" callout
- Stat bridge: 5–6 DAYS (red strikethrough) → 15–30 MINS (blue slam)
- Bridge to Part 2

### SOLUTION: DIGITIZE (2:45–3:25)
- Chapter card: "PART 2 — Document Digitization"
- PDF in → Form out promise
- LangGraph pipeline (from attached tech doc) — 4 nodes: Extract Fields → Extract Text → Analyse with LLM → Grouping
- Before/After split: cluttered PDF vs clean HTML form
- Rendered pdf-forms component mockup (sections, labels, help text)
- Built-in testing UI
- Three inputs → one component (PDF + Rules Excel + Form JSON → pdf-forms → rendered form)
- Plug & play: any framework, lightweight
- Values write back to PDF on save (circular loop diagram)
- Before/after recap

### IMPACT (3:25–3:50)
- Chapter card: "THE IMPACT — By the numbers."
- Morph animation: "5–6 DAYS" (red) morphs to "15–30 MINS" (blue) — **this is the most important animation in the video**
- 97% effort reduction stat card
- 300 fields stat card
- Fund launch timeline comparison (old long red bar vs new short green bar)
- Bandwidth unlocked: team redirected to higher-value work
- Three pillars: Speed / Intelligence / Flexibility
- Cinematic close: "One tool. End-to-end."

### CLOSE (3:50–4:00)
- Closing line: "Documents shouldn't slow you down. Paperwork makes sure they don't."
- Logo end card (hold 3s)
- Optional CTA slide

---

## SLIDE-BY-SLIDE DURATION REFERENCE

Use these exact durations — they sum to 240 seconds. Do not add or remove slides.

### INTRO (20s total)
1. 2s · 2. 2s · 3. 2s · 4. 2s · 5. 2s · 6. 3s · 7. 4s · 8. 3s

### PROBLEM: TAGGING (55s total)
9. 2s · 10. 3s · 11. 3s · 12. 3s · 13. 3s · 14. 3s · 15. 3s · 16. 3s · 17. 3s · 18. 3s · 19. 3s · 20. 3s · 21. 3s · 22. 3s · 23. 3s · 24. 3s · 25. 4s · 26. 4s

### PROBLEM: FILLING (30s total)
27. 2s · 28. 3s · 29. 3s · 30. 3s · 31. 3s · 32. 3s · 33. 3s · 34. 4s · 35. 6s

### SOLUTION: TAGGING (60s total)
36. 2s · 37. 3s · 38. 3s · 39. 3s · 40. 3s · 41. 3s · 42. 3s · 43. 3s · 44. 3s · 45. 3s · 46. 3s · 47. 3s · 48. 3s · 49. 3s · 50. 3s · 51. 3s · 52. 3s · 53. 4s · 54. 6s

### SOLUTION: DIGITIZE (40s total)
55. 2s · 56. 3s · 57. 3s · 58. 3s · 59. 3s · 60. 3s · 61. 3s · 62. 3s · 63. 3s · 64. 3s · 65. 3s · 66. 3s · 67. 5s

### IMPACT (25s total)
68. 2s · 69. 3s · 70. 3s · 71. 3s · 72. 3s · 73. 3s · 74. 3s · 75. 5s

### CLOSE (10s total)
76. 4s · 77. 3s · 78. 3s

---

## INSTRUCTIONS FOR GENERATION

1. **Generate all 78 slides.** Do not summarise, skip, or abbreviate any slide. Every slide gets the full template.

2. **Use the attached tech markdown files** as your source of truth for the technical details of both pipelines (prediction pipeline nodes, knowledge stores, LangGraph nodes, the pdf-forms component, etc.). Pull exact node names, store names, and pipeline steps from those documents.

3. **Write voiceover as it will be spoken.** Natural speech. Short punchy sentences for fast slides. Slightly longer for explanation slides. No jargon without definition. No bullet-point phrasing in the voiceover field.

4. **Describe visuals with enough detail for a designer with zero context.** For every slide: specify layout (left/right split? full screen? centred?), specific text that appears, colours, icons, mockup descriptions, diagram structures, code snippets if any.

5. **Animations are suggestions, not requirements.** The PPT generator and the user will implement them. Use natural animation language: "Zoom slam", "Wipe from left", "Fade in", "Morph", "Draw" (for arrows), "Appear staggered".

6. **Honour the section colour language:**
   - INTRO: Electric blue `#00C2FF` accents
   - PROBLEM slides: Red `#FF3B30` accents, dark red background
   - SOLUTION-TAG slides: Electric blue `#00C2FF` accents, dark blue background
   - SOLUTION-DIG slides: Green `#34C759` accents, dark green background
   - IMPACT slides: Gold `#FFD60A` accents, near-black background
   - CLOSE: Electric blue `#00C2FF`, pure black background

7. **Use a running timestamp.** Every slide header must show its exact start–end time in `M:SS–M:SS` format and its duration in seconds.

8. **Include a Style Guide section at the end** of the markdown with:
   - Colour palette table
   - Typography scale
   - Animation speed reference
   - PowerPoint export instructions
   - Morph transition setup instructions
   - Voiceover recording tips
   - Section breakdown summary table

9. **Do not add commentary or meta-text** outside of slide templates and the style guide. The file should be clean and ready for direct use.

10. **If a slide references a UI screen** (Conflict Resolver, Tag Editor, pdf-forms component, testing UI), describe the UI mockup as specifically as possible: which panels are visible, what labels appear, what interactive elements are shown, where overlays or callout arrows point.

---

## EXAMPLE — How to write one slide correctly

Here is one example slide to show the expected level of detail:

---

### Slide 1 — INTRO
**Timestamp:** 0:00–0:02 &nbsp;|&nbsp; **Duration:** 2s

#### 🖥 On Screen
Pure black screen. Nothing visible for 0.2s. Then a single line of giant bold white text slams in from the centre of the screen:

**"7 DAYS."**

Font: ~120pt, bold, white, centred. No logo. No tagline. No background elements. No border. Just the text on black.

#### 🎙 Voiceover
> Seven days.

#### ✨ Animations
- "7 DAYS." text → Zoom-In slam, 0.15s ease-out, On Click. No other animated elements.

#### ➡ Transition to Next
Cut (0s)

#### 📝 Director's Notes
Maximum shock opening. No music. No sound effect. Silence with just the text is more powerful. Hold for 1.5s after text appears before the cut. Font should feel almost uncomfortably large — it should fill most of the slide width.

---

Now generate all 78 slides at this level of detail, using the tech flows from the attached markdown files for all technical content.
