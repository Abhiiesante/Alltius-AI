import os
from alltius_ai.pdf_extractor import extract_pdf
from alltius_ai.exporters import to_markdown
from alltius_ai.plugins import run_plugins

def test_markdown_basic(tmp_path):
    sample = 'file.pdf'
    if not os.path.exists(sample):
        import pytest
        pytest.skip('No sample PDF available')
    res = extract_pdf(sample, merge_lines=True)
    md = to_markdown(res)
    assert '##' in md or '###' in md or len(md) > 0


def test_wordcount_plugin(tmp_path):
    sample = 'file.pdf'
    if not os.path.exists(sample):
        import pytest
        pytest.skip('No sample PDF available')
    res = extract_pdf(sample, merge_lines=True)
    run_plugins(res, ['wordcount'])
    found = False
    for page in res.pages:
        for block in page.content:
            if getattr(block, 'type', None) == 'paragraph':
                assert 'word_count' in block.metadata
                found = True
                break
        if found:
            break
    assert found
