# Alltius-AI PDF -> Structured JSON Extractor

## Overview
This repository provides a Python tool that parses a PDF and produces a structured JSON file preserving page hierarchy and differentiating between paragraphs, tables, and images (as chart placeholders). Basic heading detection heuristics are used to assign `section` and `sub_section` fields.

## Features
* Page-level hierarchy preserved
* Content block types: `paragraph`, `table`, `chart`, `footnote`
* Heuristic heading detection using relative font size (mode-based body font size)
* Confidence values for heading-derived blocks (size ratio heuristic)
* Table extraction via `pdfplumber`
* Image blocks included as `chart` placeholders (optional OCR excerpt)
* Footnote heuristic (bottom page region)
* Markdown export (`--markdown-out`) with tables & footnotes
* Plugin system (`--enable-plugins wordcount`) for metadata enrichment
* Parallel page processing (`--parallel`) experimental speed-up
* Command-line interface with tuning for heading detection ratio & merge heuristics

## Installation
Create and activate a virtual environment (recommended) then install requirements:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Camelot (optional enhancement for more sophisticated tables) may require system dependencies (Ghostscript, Tk, etc.) depending on platform. Current pipeline primarily uses `pdfplumber`.

## Usage
```bash
python -m alltius_ai.cli file.pdf --out output.json
```

Optional arguments:
* `--min-heading-ratio FLOAT` (default 1.15): font size ratio over median to mark heading
* `--no-pretty`: disable pretty printed JSON
* `--no-merge-lines`: disable merging consecutive lines into paragraphs
* `--log-level LEVEL`: set log verbosity (DEBUG/INFO/WARNING/ERROR)
* `--merge-gap-ratio FLOAT`: adjust vertical gap threshold for line merging
* `--enable-ocr`: run OCR on images (requires system `tesseract-ocr` installed)
* `--markdown-out PATH`: also write a Markdown rendition
* `--enable-plugins LIST`: comma-separated plugin names (e.g. `wordcount`)
* `--parallel`: process pages in parallel (experimental)

Direct module invocation:
```bash
python src/alltius_ai/pdf_extractor.py file.pdf --out output.json
```

## JSON Output Schema
Top-level object:
```json
{
	"pages": [
		{
			"page_number": 1,
			"content": [
				{
					"type": "paragraph",
					"section": "Introduction",
						"sub_section": "Background",
					"text": "Paragraph text ..."
				},
				{
					"type": "table",
					"section": null,
					"sub_section": null,
					"table_data": [["H1","H2"],["R1C1","R1C2"]],
					"description": null
				},
				{
					"type": "chart",
					"section": null,
					"sub_section": null,
					"description": "Image/Chart detected",
					"extracted_data": null
				}
			]
		}
	]
}
```

Notes:
* Ordering of blocks per page is roughly top-to-bottom using bounding boxes where available; tables currently appended with synthetic ordering if bbox unavailable.
* `chart` type currently represents any image block. Advanced OCR/chart data extraction could populate `extracted_data` later.

## Design & Heuristics
1. Text extraction uses PyMuPDF's `page.get_text("dict")` API.
2. Median span font size per page is computed; lines containing a span above `median * ratio` are treated as headings.
3. Section assignment: A heading beginning with a leading number + dot (e.g., `1.`, `2.`) is treated as a new `section`; other headings become `sub_section` if a section already exists.
4. Line merging: Consecutive line blocks with small vertical gap (<= `merge_gap_ratio` * line height, default 0.6) and same section/sub-section are merged into a single paragraph by default (disable with `--no-merge-lines`). Hyphenation at line end is resolved by concatenation without extra space.
5. Multi-level headings: Numbered patterns like `1.`, `2.3`, `3.4.5 Title` are parsed. Top-level (e.g., `1.`) becomes `section`; deeper levels become `sub_section` (currently only exposing two tiers in JSON while internally tracking a stack).
6. Table ordering: Simple heuristic attempts to position tables after proximal paragraph content using inferred y positions.
7. OCR (optional): When enabled, runs Tesseract via `pytesseract` on image blocks and appends an excerpt to the chart description if text is found.
5. Tables extracted via `pdfplumber` and cleaned (None -> empty string).
6. Images inserted as `chart` placeholders with description.

## Limitations & Future Improvements
* Heading detection may misclassify in documents with varied typography.
* Paragraph reconstruction heuristic could mis-merge or split paragraphs; configurable gap threshold could be exposed.
* Table bbox ordering: heuristic synthetic y positions when exact table bbox unavailable.
* No OCR for scanned PDFs; integrate `pytesseract` for image-based text if needed.
* Chart data extraction not implemented; placeholder for future ML/vision integration.
* Consider ML-based layout parsing (layoutparser, pdfminer.six char-level features) for higher fidelity.

## Benchmarking
Run a basic performance benchmark:
```bash
python scripts/benchmark.py file.pdf --runs 3
```

## Development / Testing
Install dev dependencies using extras:
```bash
pip install -e .[dev]
pytest -q
```

Synthetic PDF tests use ReportLab to generate controlled fixtures.

### OCR Setup
Install Tesseract on Ubuntu/Debian:
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr
```
Then run with `--enable-ocr`.

## Contributing
Feel free to open issues or PRs for enhancements (improved heading ML model, layout-based ordering, merged paragraphs, chart OCR, etc.).

## License
MIT (add a LICENSE file if distributing publicly).

---
Generated initial implementation via automated assistant.

## Markdown Export
Adds hierarchical headings (`##` sections / `###` subsections), paragraphs, tables in GFM format, charts as blockquotes, and per-page footnotes under a `#### Footnotes` heading.

## Plugins
Plugin interface (`plugins.py`) allows post-processing of the `ExtractionResult`. A sample `wordcount` plugin annotates paragraphs with `word_count` metadata. Enable via:
```bash
alltius-extract file.pdf --out out.json --enable-plugins wordcount
```

## Parallel Processing
Use `--parallel` to parse pages concurrently. Order is preserved after aggregation. Beneficial for large multi-page PDFs. May not significantly speed up OCR-heavy workloads due to GIL/IO balance but can help with pure parsing.