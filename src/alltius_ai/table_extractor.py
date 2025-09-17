from __future__ import annotations
from typing import List
import pdfplumber


def extract_tables(pdf_path: str) -> dict:
    tables = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_tables = []
            try:
                extracted = page.extract_tables() or []
                for tbl in extracted:
                    cleaned = [[cell if cell is not None else '' for cell in row] for row in tbl]
                    page_tables.append(cleaned)
            except Exception:
                continue
            if page_tables:
                tables[i] = page_tables
    return tables
