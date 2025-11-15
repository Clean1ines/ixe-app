"""
Integration tests for the updated BrowserManager.
The BrowserManager now creates/closes a page for each get_page_content call.
"""
import pytest
import pytest_asyncio
import asyncio
from src.infrastructure.browser_management.browser_manager import BrowserManager

@pytest_asyncio.fixture
async def browser_manager():
    """Fixture to create and initialize a BrowserManager."""
    bm = BrowserManager()
    await bm.initialize()
    yield bm
    await bm.close()

@pytest.mark.asyncio
async def test_browser_manager_initialize_and_close():
    """Test that BrowserManager initializes and closes correctly."""
    bm = BrowserManager()
    assert not bm._initialized
    assert bm._browser is None
    # _page больше не существует, убираем проверку

    await bm.initialize()
    assert bm._initialized
    assert bm._browser is not None
    # _page больше не существует, убираем проверку

    await bm.close()
    assert not bm._initialized
    assert bm._browser is None

@pytest.mark.asyncio
async def test_browser_manager_get_page_content(browser_manager):
    """Test that BrowserManager can get page content with a new page per call."""
    url = "https://httpbin.org/html"  # A simple page for testing
    content = await browser_manager.get_page_content(url)

    assert content is not None
    assert isinstance(content, str)
    assert "Herman Melville - Moby-Dick" in content or "<html>" in content  # Basic check

@pytest.mark.asyncio
async def test_browser_manager_get_page_content_timeout(browser_manager):
    """Test that BrowserManager handles timeout correctly with a new page per call."""
    url = "https://httpbin.org/delay/5"
    timeout = 1

    with pytest.raises(Exception): # Expecting a timeout exception
        await browser_manager.get_page_content(url, timeout=timeout)

@pytest.mark.asyncio
async def test_browser_manager_is_healthy(browser_manager):
    """Test that BrowserManager's health check works."""
    is_healthy_before_close = await browser_manager.is_healthy()
    assert is_healthy_before_close

    await browser_manager.close()
    is_healthy_after_close = await browser_manager.is_healthy()
    assert not is_healthy_after_close

# Test concurrent access *within* a single BrowserManager (not the pool)
@pytest.mark.asyncio
async def test_browser_manager_concurrent_page_requests(browser_manager):
    """Test that a single BrowserManager can handle concurrent page requests by creating multiple pages."""
    urls = ["https://httpbin.org/uuid"] * 3 # UUID endpoint is relatively quick

    start_time = asyncio.get_event_loop().time()
    # Each call to get_page_content creates a new page, so these should run more independently within the browser
    tasks = [browser_manager.get_page_content(url, timeout=10) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = asyncio.get_event_loop().time()

    duration = end_time - start_time
    # Duration depends heavily on network and httpbin speed, but creating new pages should allow some concurrency within the browser.
    # It might still be sequential if httpbin is slow, but theoretically faster than sharing one page.
    print(f"Single BrowserManager concurrent requests took {duration:.2f} seconds for 3 URLs.")
    # We mainly check that no exceptions unrelated to timeout/network occurred
    for result in results:
        if isinstance(result, Exception):
            print(f"Task resulted in exception: {result}")
            # If it's a timeout or network error, it's okay for this test context.
            # Re-raise other unexpected exceptions
            if not isinstance(result, (asyncio.TimeoutError, ConnectionError)):
                 raise result
        else:
            assert isinstance(result, str)
            assert len(result) > 0
