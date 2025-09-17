from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
import logging

from .models import ExtractionResult, PageResult, ParagraphBlock, TableBlock, ChartBlock
from .models import FootnoteBlock
from .heading_detection import detect_headings, assign_sections
from .table_extractor import extract_tables


def extract_pdf(
    pdf_path: str,
    min_heading_ratio: float = 1.15,
    logger: logging.Logger | None = None,
    merge_lines: bool = True,
    merge_gap_ratio: float = 0.6,
    enable_ocr: bool = False,
    parallel: bool = False,
) -> ExtractionResult:
    logger = logger or logging.getLogger(__name__)
    logger.debug("Opening PDF: %s", pdf_path)
    pdf_path = str(pdf_path)
    doc = fitz.open(pdf_path)

    # Pre-extract tables with pdfplumber
    table_map = extract_tables(pdf_path)
    logger.debug("Extracted tables for %d pages", len(table_map))

    pages: List[PageResult] = []
    headings_per_page = {}
    raw_paragraphs: List[Tuple[str,int,Tuple[float,float,float,float]]] = []

    def _process_page(page_index: int):
        page = doc[page_index]
        page_number = page_index + 1
        page_dict = page.get_text("dict")
        headings = detect_headings(page_dict, min_ratio=min_heading_ratio)
        local_headings = [(h[0], h[1]) for h in headings]
        local_paragraphs: List[Tuple[str,int,Tuple[float,float,float,float]]] = []
        for block in page_dict.get("blocks", []):
            btype = block.get("type", 0)
            if btype == 0:  # text
                for line in block.get("lines", []):
                    line_text_parts = [span.get("text", "") for span in line.get("spans", [])]
                    text_line = "".join(line_text_parts).strip()
                    if text_line:
                        bbox = line.get("spans", [])[0].get("bbox", (0,0,0,0)) if line.get("spans") else (0,0,0,0)
                        local_paragraphs.append((text_line, page_number, bbox))
            elif btype == 1:  # image block => potential chart placeholder
                bbox = block.get("bbox", (0,0,0,0))
                desc = "Image/Chart detected"
                if enable_ocr:
                    try:
                        import io
                        from PIL import Image
                        import pytesseract
                        for img in page.get_images(full=True):
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            if pix.n > 4:
                                pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_bytes = pix.tobytes("png")
                            image = Image.open(io.BytesIO(img_bytes))
                            ocr_text = pytesseract.image_to_string(image).strip()
                            if ocr_text:
                                desc = f"Image/Chart detected (OCR excerpt: {ocr_text[:60]}...)"
                                break
                    except Exception as e:
                        logger.debug("OCR failed: %s", e)
                local_paragraphs.append((f"__IMG_BLOCK__::{desc}", page_number, bbox))
        return page_number, local_headings, local_paragraphs

    if parallel and len(doc) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as ex:
            for page_number, local_headings, local_paragraphs in ex.map(_process_page, range(len(doc))):
                headings_per_page[page_number] = local_headings
                raw_paragraphs.extend(local_paragraphs)
                pages.append(PageResult(page_number=page_number))
    else:
        for page_index in range(len(doc)):
            page_number, local_headings, local_paragraphs = _process_page(page_index)
            headings_per_page[page_number] = local_headings
            raw_paragraphs.extend(local_paragraphs)
            pages.append(PageResult(page_number=page_number))

    # Assign section/subsection
    assigned = assign_sections(raw_paragraphs, headings_per_page)

    # Build paragraph blocks per page
    page_para_blocks = {p.page_number: [] for p in pages}
    image_placeholders = {p.page_number: [] for p in pages}
    for ((text, page_number, bbox), (_assigned_text, section, subsection)) in zip(raw_paragraphs, assigned):
        if text.startswith("__IMG_BLOCK__::"):
            desc = text.split("::",1)[1]
            image_placeholders[page_number].append((bbox, ChartBlock(type="chart", page_number=page_number, section=section, sub_section=subsection, description=desc)))
        else:
            # assign confidence if this exact text was a heading recognized earlier
            conf = None
            block = ParagraphBlock(type="paragraph", page_number=page_number, section=section, sub_section=subsection, text=text, bbox=bbox)
            page_para_blocks[page_number].append((bbox, block))

    if merge_lines:
        for page_no, items in page_para_blocks.items():
            if not items:
                continue
            merged = []
            # sort by vertical position
            items.sort(key=lambda x: (x[0][1], x[0][0]))
            current_block = None
            last_y_bottom = None
            for bbox, block in items:
                y0, y1 = bbox[1], bbox[3]
                if current_block is None:
                    current_block = block
                    last_y_bottom = y1
                    continue
                gap = y0 - (last_y_bottom or y0)
                line_height = y1 - y0 if (y1 - y0) > 0 else 1
                if gap <= line_height * merge_gap_ratio and block.section == current_block.section and block.sub_section == current_block.sub_section:
                    if current_block.text.endswith('-'):
                        current_block.text = current_block.text[:-1] + block.text.lstrip()
                    else:
                        current_block.text += ' ' + block.text
                    last_y_bottom = y1
                else:
                    merged.append(current_block)
                    current_block = block
                    last_y_bottom = y1
            if current_block is not None:
                merged.append(current_block)
            # replace with merged, reattach synthetic bbox ordering using original first bbox
            page_para_blocks[page_no] = [((b.bbox or (0,0,0,0)), b) for b in merged]
    for page_index in range(len(doc)):
        page_number = page_index + 1
        page = doc[page_index]
        page_height = page.rect.height
        bottom_threshold = page_height * 0.9
        new_items = []
        for bbox, block in page_para_blocks.get(page_number, []):
            if bbox[1] >= bottom_threshold:
                foot = FootnoteBlock(type="footnote", page_number=page_number, section=block.section, sub_section=block.sub_section, text=block.text, confidence=0.5, metadata={"source":"heuristic"})
                new_items.append((bbox, foot))
            else:
                new_items.append((bbox, block))
        page_para_blocks[page_number] = new_items
    for p in pages:
        positional_items = []
        para_items = page_para_blocks.get(p.page_number, [])
        if p.page_number in table_map:
            if para_items:
                min_y = min(b[0][1] for b in para_items)
                max_y = max(b[0][3] for b in para_items)
            else:
                min_y, max_y = 0, 0
            spread = max(max_y - min_y, 1)
            per_table_offset = spread / (len(table_map[p.page_number]) + 1)
            for idx, tbl in enumerate(table_map[p.page_number], start=1):
                y_center = min_y + per_table_offset * idx if spread > 1 else 99999
                bbox = (0, y_center, 0, y_center + 1)
                positional_items.append((bbox, TableBlock(type="table", page_number=p.page_number, table_data=tbl, bbox=bbox)))
        positional_items.extend(para_items)
        positional_items.extend(image_placeholders.get(p.page_number, []))
        positional_items.sort(key=lambda item: (item[0][1], item[0][0]))
        p.content.extend([blk for _bbox, blk in positional_items])
        logger.debug("Page %d: %d content blocks", p.page_number, len(p.content))

    return ExtractionResult(pages=pages)


def save_extraction(result: ExtractionResult, output_path: str, pretty: bool = True):
    data = result.to_dict()
    with open(output_path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract structured JSON from PDF")
    parser.add_argument("pdf_path", help="Path to input PDF")
    parser.add_argument("--out", default="output.json", help="Output JSON file path")
    parser.add_argument("--min-heading-ratio", type=float, default=1.15, help="Font size ratio above median to consider a heading")
    parser.add_argument("--no-pretty", action="store_true", help="Disable pretty JSON formatting")
    parser.add_argument("--no-merge-lines", action="store_true", help="Disable merging of consecutive lines into paragraphs")
    parser.add_argument("--merge-gap-ratio", type=float, default=0.6, help="Gap ratio (relative to line height) threshold for line merging")
    parser.add_argument("--enable-ocr", action="store_true", help="Enable OCR on images (requires pytesseract & tesseract-ocr)")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    res = extract_pdf(
        args.pdf_path,
        min_heading_ratio=args.min_heading_ratio,
        merge_lines=not args.no_merge_lines,
        merge_gap_ratio=args.merge_gap_ratio,
        enable_ocr=args.enable_ocr,
    )
    save_extraction(res, args.out, pretty=not args.no_pretty)
    print(f"Extraction complete: {args.out}")
