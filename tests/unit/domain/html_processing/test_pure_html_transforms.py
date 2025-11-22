import pytest
from pathlib import Path
from src.domain.html_processing.pure_html_transforms import (
    extract_dom_tree,
    extract_block_pairs,
    transform_blocks_to_raw_data,
)

SIMPLE_HTML = '''
<html>
  <body>
    <div class="problem-header" data-task-id="t1"><h3>Задача 1</h3></div>
    <div class="problem-body"><p>Текст задачи 1</p></div>

    <div class="problem-header" data-task-id="t2"><h3>Задача 2</h3></div>
    <div class="problem-body"><p>Текст задачи 2</p></div>
  </body>
</html>
'''

def test_extract_dom_tree_returns_bs_object():
    dom = extract_dom_tree("<html><body>ok</body></html>")
    assert dom is not None
    assert dom.find("body").get_text(strip=True) == "ok"

def test_extract_block_pairs_finds_header_body_pairs():
    pairs = extract_block_pairs(SIMPLE_HTML)
    assert isinstance(pairs, list)
    assert len(pairs) == 2
    # first pair contains header and body
    header0, body0 = pairs[0]
    assert "Задача 1" in header0
    assert "Текст задачи 1" in body0

def test_transform_blocks_to_raw_data_extracts_task_id_and_title():
    pairs = extract_block_pairs(SIMPLE_HTML)
    raw = transform_blocks_to_raw_data(pairs)
    assert isinstance(raw, list)
    assert len(raw) == 2
    assert raw[0]["task_id"] == "t1"
    assert "Задача 1" in raw[0]["title"]
