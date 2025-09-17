from __future__ import annotations
from .models import ExtractionResult, ParagraphBlock, TableBlock, ChartBlock, FootnoteBlock
from typing import List

def _render_table(table: List[List[str]]) -> str:
    if not table:
        return ""
    header = table[0]
    body = table[1:]
    line_header = "| " + " | ".join(cell.strip() for cell in header) + " |"
    line_sep = "| " + " | ".join(["---"] * len(header)) + " |"
    lines = [line_header, line_sep]
    for row in body:
        lines.append("| " + " | ".join(cell.strip() for cell in row) + " |")
    return "\n".join(lines)

def to_markdown(result: ExtractionResult) -> str:
    md_parts: List[str] = []
    last_section = None
    last_sub = None
    for page in result.pages:
        for block in page.content:
            if isinstance(block, ParagraphBlock):
                if block.section and block.section != last_section:
                    md_parts.append(f"## {block.section}")
                    last_section = block.section
                    last_sub = None
                if block.sub_section and block.sub_section != last_sub:
                    md_parts.append(f"### {block.sub_section}")
                    last_sub = block.sub_section
                md_parts.append(block.text)
                md_parts.append("")
            elif isinstance(block, TableBlock):
                if block.section and block.section != last_section:
                    md_parts.append(f"## {block.section}")
                    last_section = block.section
                    last_sub = None
                if block.sub_section and block.sub_section != last_sub:
                    md_parts.append(f"### {block.sub_section}")
                    last_sub = block.sub_section
                if block.description:
                    md_parts.append(f"_Table: {block.description}_")
                md_parts.append(_render_table(block.table_data))
                md_parts.append("")
            elif isinstance(block, ChartBlock):
                if block.section and block.section != last_section:
                    md_parts.append(f"## {block.section}")
                    last_section = block.section
                    last_sub = None
                if block.sub_section and block.sub_section != last_sub:
                    md_parts.append(f"### {block.sub_section}")
                    last_sub = block.sub_section
                desc = block.description or "Chart"
                md_parts.append(f"> {desc}")
                md_parts.append("")
            elif isinstance(block, FootnoteBlock):
                pass
        footnotes = [b for b in page.content if isinstance(b, FootnoteBlock)]
        if footnotes:
            md_parts.append("#### Footnotes")
            for idx, fn in enumerate(footnotes, start=1):
                md_parts.append(f"[{idx}] {fn.text}")
            md_parts.append("")
    return "\n".join(md_parts).strip() + "\n"
