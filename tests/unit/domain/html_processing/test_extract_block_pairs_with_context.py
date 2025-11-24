"""
Unit tests for extract_block_pairs function with real FIPI page structure.
Tests the scenario with a common qblock without ID followed by qblocks with IDs.
"""
import pytest
from src.domain.html_processing.pure_html_transforms import extract_block_pairs

class TestExtractBlockPairsWithContext:

    def test_extract_block_pairs_with_common_qblock(self):
        """Test extraction when there's a common qblock without ID followed by qblocks with IDs."""
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
                    <table class="task-info-panel">
                        <tr><td>КЭС:</td><td>1.1.1</td></tr>
                        <tr><td>Тип ответа:</td><td>Краткий ответ</td></tr>
                    </table>
                </div>
                <div class="cell_0">Какой вывод можно сделать из текста?</div>
                <input type="text" name="answer_1" />
            </div>
            
            <div class="qblock" id="q002">
                <div class="task-header-panel">
                    <span class="id-text"><span class="canselect">2</span></span>
                    <table class="task-info-panel">
                        <tr><td>КЭС:</td><td>1.2.3</td></tr>
                        <tr><td>Тип ответа:</td><td>Краткий ответ</td></tr>
                    </table>
                </div>
                <div class="cell_0">Найдите в тексте пример использования аллюзии.</div>
                <input type="text" name="answer_2" />
            </div>
        </body>
        </html>
        """
        pairs = extract_block_pairs(html)
        
        # Should create ONE pair for the group of individual qblocks with the common context
        # In our new implementation with grouping, all qblocks after a common context are combined
        assert len(pairs) == 1  # One combined pair for the group
        header, body = pairs[0]
        
        assert 'i001' in header  # Should create a header with the ID of the first qblock in the group
        assert 'Общее задание' in body    # Should contain the common context
        assert 'q001' in body    # Should contain the first qblock
        assert 'q002' in body    # Should contain the second qblock

    def test_extract_block_pairs_without_common_qblock(self):
        """Test extraction when there are only individual qblocks with IDs."""
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
        
        assert len(pairs) == 2
        header1, body1 = pairs[0]
        header2, body2 = pairs[1]
        
        assert 'i001' in header1
        assert 'q001' in body1
        assert 'i002' in header2
        assert 'q002' in body2

    def test_extract_block_pairs_empty_page(self):
        """Test extraction with an empty page."""
        html = ""
        pairs = extract_block_pairs(html)
        
        assert pairs == []

    def test_extract_block_pairs_no_qblocks(self):
        """Test extraction when there are no qblocks."""
        html = """
        <html>
        <body>
            <div>Just some random content</div>
        </body>
        </html>
        """
        pairs = extract_block_pairs(html)
        
        assert pairs == []
