"""Refactored tests for IframeHandler using fakes instead of mocks"""
import pytest
from bs4 import BeautifulSoup

from src.infrastructure.services.page_scraping.components.iframe_handler import IframeHandler
from tests.fakes import FakeBrowserPage


class TestIframeHandlerRefactored:
    """Test suite for IframeHandler using fakes"""
    
    @pytest.fixture
    def handler(self):
        return IframeHandler()
    
    @pytest.fixture
    def fake_page(self):
        return FakeBrowserPage(url="https://fipi.ru/page1")
    
    @pytest.fixture
    def main_content_with_iframe(self):
        return """
        <html>
            <body>
                <iframe id="questions_container" src="/iframe/content"></iframe>
                <div>Main content</div>
            </body>
        </html>
        """.strip() # Убираем внешние пробелы
    
    @pytest.fixture
    def main_content_without_iframe(self):
        return """
        <html>
            <body>
                <div>Main content without iframe</div>
            </body>
        </html>
        """.strip()
    
    @pytest.fixture
    def main_content_with_iframe_no_src(self):
        return """
        <html>
            <body>
                <iframe id="questions_container"></iframe>
                <div>Main content</div>
            </body>
        </html>
        """.strip()
    
    @pytest.fixture
    def iframe_content(self):
        return """
        <html>
            <body>
                <div>Iframe specific content</div>
                <question>Question 1</question>
            </body>
        </html>
        """.strip()

    @pytest.mark.asyncio
    async def test_handle_iframe_with_valid_src(self, handler, fake_page, main_content_with_iframe, iframe_content):
        """Test handling iframe with valid src attribute using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 30
        
        # Setup fake page content
        fake_page.set_content_for_url(url, main_content_with_iframe)
        fake_page.set_content_for_url("https://fipi.ru/iframe/content", iframe_content)
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content_with_iframe
        )
        
        # Assert - используем .strip() для надежного сравнения
        assert actual_content.strip() == iframe_content.strip()
        assert source_url == "https://fipi.ru/iframe/content"
        
        # Verify interactions
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1
        assert goto_calls[0]['url'] == "https://fipi.ru/iframe/content"
        assert goto_calls[0]['timeout'] == 30000

    @pytest.mark.asyncio
    async def test_handle_iframe_without_src(self, handler, fake_page, main_content_with_iframe_no_src):
        """Test handling iframe without src attribute using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 30
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content_with_iframe_no_src
        )
        
        # Assert
        assert actual_content == main_content_with_iframe_no_src
        assert source_url == url
        assert len(fake_page.get_goto_calls()) == 0

    @pytest.mark.asyncio
    async def test_handle_iframe_with_navigation_error(self, handler, fake_page, main_content_with_iframe):
        """Test fallback when iframe navigation fails using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 30
        
        # Setup: main URL has content, but iframe URL is not setup (will cause navigation error)
        fake_page.set_content_for_url(url, main_content_with_iframe)
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content_with_iframe
        )
        
        # Assert - should fallback to main content
        assert actual_content == main_content_with_iframe
        assert source_url == url # Должен вернуться исходный URL
        
        # Should attempt navigation to iframe URL (which fails)
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1
        assert goto_calls[0]['url'] == "https://fipi.ru/iframe/content"

    @pytest.mark.asyncio
    async def test_handle_iframe_not_found(self, handler, fake_page, main_content_without_iframe):
        """Test handling when no iframe is present using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 30
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content_without_iframe
        )
        
        # Assert
        assert actual_content == main_content_without_iframe
        assert source_url == url
        assert len(fake_page.get_goto_calls()) == 0

    @pytest.mark.asyncio
    async def test_handle_iframe_with_different_base_url(self, handler, fake_page):
        """Test iframe URL construction with different base URLs using fake"""
        # Arrange
        main_content = '<html><iframe id="questions_container" src="/relative/path"></iframe></html>'
        url = "https://example.com/base/page"
        timeout = 30
        
        fake_page.set_content_for_url(url, main_content)
        fake_page.set_content_for_url("https://example.com/relative/path", "<html>Iframe content</html>")
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content
        )
        
        # Assert
        assert source_url == "https://example.com/relative/path"
        
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1
        assert goto_calls[0]['url'] == "https://example.com/relative/path"

    def test_find_questions_iframe_found(self, handler, main_content_with_iframe):
        """Test finding questions iframe when present"""
        # Arrange
        soup = BeautifulSoup(main_content_with_iframe, "html.parser")
        
        # Act
        iframe = handler.find_questions_iframe(soup)
        
        # Assert
        assert iframe is not None
        assert iframe.get("id") == "questions_container"
        assert iframe.get("src") == "/iframe/content"

    def test_find_questions_iframe_not_found(self, handler, main_content_without_iframe):
        """Test finding questions iframe when not present"""
        # Arrange
        soup = BeautifulSoup(main_content_without_iframe, "html.parser")
        
        # Act
        iframe = handler.find_questions_iframe(soup)
        
        # Assert
        assert iframe is None

    def test_find_questions_iframe_wrong_id(self, handler):
        """Test finding questions iframe with different ID"""
        # Arrange
        content = '<html><iframe id="wrong_id" src="/test"></iframe></html>'
        soup = BeautifulSoup(content, "html.parser")
        
        # Act
        iframe = handler.find_questions_iframe(soup)
        
        # Assert
        assert iframe is None

    @pytest.mark.asyncio
    async def test_handle_iframe_preserves_original_content_on_error(self, handler, fake_page, main_content_with_iframe):
        """Test that original content is preserved when iframe handling fails using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 30
        original_content = main_content_with_iframe
        
        fake_page.set_content_for_url(url, original_content)
        await fake_page.set_current_url(url)
        # iframe URL not setup - will cause navigation error
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, original_content
        )
        
        # Assert
        assert actual_content == original_content
        assert source_url == url 
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1

    @pytest.mark.asyncio
    async def test_handle_iframe_with_absolute_src_url(self, handler, fake_page):
        """Test handling iframe with absolute URL in src using fake"""
        # Arrange
        main_content = '<html><iframe id="questions_container" src="https://absolute.com/path"></iframe></html>'
        url = "https://fipi.ru/page1"
        timeout = 30
        
        fake_page.set_content_for_url(url, main_content)
        fake_page.set_content_for_url("https://absolute.com/path", "<html>Absolute iframe content</html>")
        await fake_page.set_current_url(url)
        
        # Act
        actual_content, source_url = await handler.handle_iframe_content(
            fake_page, url, timeout, main_content
        )
        
        # Assert
        assert source_url == "https://absolute.com/path"
        
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1
        assert goto_calls[0]['url'] == "https://absolute.com/path"

    @pytest.mark.asyncio
    async def test_handle_iframe_respects_custom_timeout(self, handler, fake_page, main_content_with_iframe):
        """Test that custom timeout values are respected using fake"""
        # Arrange
        url = "https://fipi.ru/page1"
        timeout = 15  # Different from default
        
        fake_page.set_content_for_url(url, main_content_with_iframe)
        fake_page.set_content_for_url("https://fipi.ru/iframe/content", "<html>Iframe content</html>")
        await fake_page.set_current_url(url)
        
        # Act
        await handler.handle_iframe_content(fake_page, url, timeout, main_content_with_iframe)
        
        # Assert
        goto_calls = fake_page.get_goto_calls()
        assert len(goto_calls) == 1
        assert goto_calls[0]['timeout'] == 15000  # 15 seconds in milliseconds
