import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from alltius_ai.pdf_extractor import extract_pdf

def make_pdf(tmp_path: Path):
    p = tmp_path / "sample.pdf"
    c = canvas.Canvas(str(p), pagesize=LETTER)
    # Simulate heading (larger font)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(72, 720, "1. Introduction")
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, "This is a test paragraph line one.")
    c.drawString(72, 685, "Continues on line two.")
    c.showPage()
    c.save()
    return p


def test_basic_extraction(tmp_path):
    pdf_file = make_pdf(tmp_path)
    result = extract_pdf(str(pdf_file))
    data = result.to_dict()
    assert 'pages' in data
    assert len(data['pages']) == 1
    page = data['pages'][0]
    assert page['page_number'] == 1
    # One section should be detected
    paragraphs = [b for b in page['content'] if b['type'] == 'paragraph']
    assert any(p.get('section','').startswith('1.') for p in paragraphs)
    # Merged paragraph should contain both lines
    merged_texts = [p['text'] for p in paragraphs]
    assert any('line one' in t and 'line two' in t for t in merged_texts)
