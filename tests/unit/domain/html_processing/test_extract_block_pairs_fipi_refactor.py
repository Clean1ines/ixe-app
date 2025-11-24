"""
Unit tests for extract_block_pairs function refactoring using classical TDD.
These tests verify the new FIPI-specific logic for qblock extraction with grouping.
"""
from src.domain.html_processing.pure_html_transforms import extract_block_pairs

def test_extract_block_pairs_finds_qblocks_with_ids():
    """Test that extract_block_pairs finds qblocks with IDs and creates proper header-body pairs."""
    html = """
    <html>
      <body>
        <div class="qblock" id="q001">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">1</span></span>
          </div>
          <div class="cell_0">Задание 1.</div>
        </div>
        <div class="qblock" id="q002">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">2</span></span>
          </div>
          <div class="cell_0">Задание 2.</div>
        </div>
      </body>
    </html>
    """
    pairs = extract_block_pairs(html)
    
    assert isinstance(pairs, list)
    assert len(pairs) == 2
    
    # Check first pair
    header0, body0 = pairs[0]
    assert 'i001' in header0  # Header should contain the ID without 'q'
    assert 'q001' in body0    # Body should contain the full qblock
    assert 'Задание 1.' in body0
    
    # Check second pair
    header1, body1 = pairs[1]
    assert 'i002' in header1
    assert 'q002' in body1
    assert 'Задание 2.' in body1


def test_extract_block_pairs_handles_common_context_single_window():
    """Test that extract_block_pairs handles a single common context correctly."""
    html = """
    <html>
      <body>
        <!-- Common qblock without ID - contains shared context -->
        <div class="qblock">
          <div class="cell_0">Общее задание: Прочитайте текст и выполните задания 1-3.</div>
          <img src="common_image.png" />
        </div>
        
        <!-- Individual qblocks with IDs -->
        <div class="qblock" id="q001">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">1</span></span>
          </div>
          <div class="cell_0">Какой вывод можно сделать из текста?</div>
        </div>
        
        <div class="qblock" id="q002">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">2</span></span>
          </div>
          <div class="cell_0">Найдите в тексте пример использования аллюзии.</div>
        </div>
      </body>
    </html>
    """
    pairs = extract_block_pairs(html)
    
    # Should create ONE pair for the group of qblocks with common context
    assert len(pairs) == 1
    
    # The pair should contain the common context and both individual qblocks
    header, body = pairs[0]
    
    assert 'i001' in header  # Header should contain the ID of the first qblock in the group
    assert 'Общее задание' in body
    assert 'q001' in body
    assert 'Какой вывод' in body
    assert 'q002' in body
    assert 'Найдите в тексте' in body


def test_extract_block_pairs_handles_multiple_common_contexts():
    """Test that extract_block_pairs handles multiple common contexts correctly."""
    html = """
    <html>
      <body>
        <!-- First common qblock -->
        <div class="qblock">
          <div class="cell_0">Общее задание 1: Прочитайте текст A и выполните задания 1-2.</div>
        </div>
        
        <!-- Individual qblocks for first context -->
        <div class="qblock" id="q001">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">1</span></span>
          </div>
          <div class="cell_0">Вопрос к тексту A 1.</div>
        </div>
        
        <div class="qblock" id="q002">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">2</span></span>
          </div>
          <div class="cell_0">Вопрос к тексту A 2.</div>
        </div>
        
        <!-- Second common qblock -->
        <div class="qblock">
          <div class="cell_0">Общее задание 2: Прочитайте текст B и выполните задания 3-4.</div>
        </div>
        
        <!-- Individual qblocks for second context -->
        <div class="qblock" id="q003">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">3</span></span>
          </div>
          <div class="cell_0">Вопрос к тексту B 1.</div>
        </div>
        
        <div class="qblock" id="q004">
          <div class="task-header-panel">
            <span class="id-text"><span class="canselect">4</span></span>
          </div>
          <div class="cell_0">Вопрос к тексту B 2.</div>
        </div>
      </body>
    </html>
    """
    pairs = extract_block_pairs(html)
    
    # Should create TWO pairs: one for each common context + its qblocks
    assert len(pairs) == 2
    
    # First pair should have first common context and its qblocks
    header1, body1 = pairs[0]
    
    assert 'i001' in header1  # Header should contain the ID of the first qblock in the first group
    assert 'Общее задание 1' in body1
    assert 'q001' in body1
    assert 'Вопрос к тексту A 1' in body1
    assert 'q002' in body1
    assert 'Вопрос к тексту A 2' in body1
    
    # Second pair should have second common context and its qblocks
    header2, body2 = pairs[1]
    
    assert 'i003' in header2  # Header should contain the ID of the first qblock in the second group
    assert 'Общее задание 2' in body2
    assert 'q003' in body2
    assert 'Вопрос к тексту B 1' in body2
    assert 'q004' in body2
    assert 'Вопрос к тексту B 2' in body2


def test_extract_block_pairs_empty_page():
    """Test that extract_block_pairs returns empty list for empty page."""
    html = ""
    pairs = extract_block_pairs(html)
    
    assert pairs == []


def test_extract_block_pairs_no_qblocks():
    """Test that extract_block_pairs returns empty list when no qblocks found."""
    html = """
    <html>
      <body>
        <div>Just some random content</div>
        <p>Another random element</p>
      </body>
    </html>
    """
    pairs = extract_block_pairs(html)
    
    assert pairs == []


def test_extract_block_pairs_qblocks_without_ids():
    """Test that extract_block_pairs handles qblocks without IDs (common context only)."""
    html = """
    <html>
      <body>
        <div class="qblock">
          <div class="cell_0">Common context without ID.</div>
        </div>
        <div>Some other content</div>
      </body>
    </html>
    """
    pairs = extract_block_pairs(html)
    
    # Should return empty list as there are no qblocks with IDs (individual tasks)
    assert pairs == []
