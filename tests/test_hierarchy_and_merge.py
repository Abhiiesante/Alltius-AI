import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from alltius_ai.pdf_extractor import extract_pdf


def build_pdf(path: Path):
    c = canvas.Canvas(str(path), pagesize=LETTER)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 730, "1. Overview")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 705, "1.1 Details")
    c.setFont("Helvetica", 12)
    c.drawString(72, 685, "First line of paragraph.")
    c.drawString(72, 670, "Second line merges.")
    c.showPage()
    c.save()


def test_hierarchy_and_merge(tmp_path):
    pdf_file = tmp_path / "hier.pdf"
    build_pdf(pdf_file)
    result = extract_pdf(str(pdf_file), merge_gap_ratio=0.8)
    data = result.to_dict()
    page = data['pages'][0]
    paras = [b for b in page['content'] if b['type'] == 'paragraph']
    assert any('First line' in p['text'] and 'Second line' in p['text'] for p in paras)
    assert any(p['section'] and p['section'].startswith('1.') for p in paras)
    assert any(p['sub_section'] and p['sub_section'].startswith('1.1') for p in paras)
