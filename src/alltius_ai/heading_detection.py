from __future__ import annotations
from typing import List, Tuple, Optional
import re


def detect_headings(page_dict: dict, min_ratio: float = 1.15) -> List[Tuple[str, Tuple[float,float,float,float], float]]:
    spans = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                txt = span.get("text", "").strip()
                if not txt:
                    continue
                spans.append(span.get("size", 0))
    if not spans:
        return []
    from collections import Counter
    counter = Counter(spans)
    body_size, body_freq = counter.most_common(1)[0]
    if body_freq == 1:
        spans_sorted = sorted(spans)
        body_size = spans_sorted[len(spans_sorted)//2]
    threshold = body_size * min_ratio

    headings: List[Tuple[str, Tuple[float,float,float,float], float]] = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            line_text_parts = []
            max_size = 0
            bbox = None
            for span in line.get("spans", []):
                txt = span.get("text", "").strip()
                if not txt:
                    continue
                size = span.get("size", 0)
                if size > max_size:
                    max_size = size
                if bbox is None:
                    bbox = span.get("bbox", (0,0,0,0))
                line_text_parts.append(txt)
            if not line_text_parts:
                continue
            if max_size >= threshold:
                text_line = " ".join(line_text_parts)
                confidence = (max_size / body_size) if body_size else 1.0
                headings.append((text_line, bbox, round(confidence, 3)))
    return headings


def assign_sections(paragraphs: List[Tuple[str, int, Tuple[float,float,float,float]]], headings_per_page: dict) -> List[Tuple[str, Optional[str], Optional[str]]]:
    results = []
    last_section = None
    last_subsection = None
    for text, page, bbox in paragraphs:
        y_top = bbox[1] if bbox else 0
        candidates = []
        for h_text, h_bbox in headings_per_page.get(page, []):
            if h_bbox and h_bbox[1] <= y_top:
                candidates.append((h_text, h_bbox))
        if candidates:
            candidates.sort(key=lambda x: x[1][1])  # ascending y
            level_map = {}  # level -> text
            last_plain = None
            for h_text, _hb in candidates:
                m = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)$", h_text)
                if m:
                    numbering = m.group(1)
                    level = numbering.count('.') + 1
                    level_map[level] = h_text
                else:
                    last_plain = h_text
            # Determine section/subsection
            if level_map:
                # section is level 1 if present
                last_section = level_map.get(1, last_section)
                # sub_section is highest level >1 if exists
                deeper_levels = [lvl for lvl in level_map.keys() if lvl > 1]
                if deeper_levels:
                    top_deep = max(deeper_levels)
                    last_subsection = level_map[top_deep]
                else:
                    last_subsection = None
                if last_plain and last_section:
                    if last_plain != last_section:
                        last_subsection = last_plain
                elif last_plain and not level_map.get(1):
                    if last_section is None:
                        last_section = last_plain
                    else:
                        last_subsection = last_plain
            else:
                if last_plain:
                    if last_section is None:
                        last_section = last_plain
                        last_subsection = None
                    else:
                        last_subsection = last_plain
        results.append((text, last_section, last_subsection))
    return results
