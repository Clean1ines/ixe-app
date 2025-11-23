"""
Integration tests for the BrowserManager.
"""
import pytest
import pytest_asyncio
import asyncio
import time
from src.infrastructure.browser_management.browser_manager import BrowserManager

@pytest_asyncio.fixture
async def browser_manager():
    bm = BrowserManager()
    await bm.initialize()
    yield bm
    await bm.close()

@pytest.mark.asyncio
async def test_browser_manager_initialize_and_close():
    bm = BrowserManager()
    assert not bm._initialized
    assert bm._browser is None

    await bm.initialize()
    assert bm._initialized
    assert bm._browser is not None

    await bm.close()
    assert not bm._initialized
    assert bm._browser is None

@pytest.mark.asyncio
async def test_browser_manager_get_page_content(browser_manager):
    # Используем надежный URL
    url = "https://example.com"
    content = await browser_manager.get_page_content(url, timeout=15)

    assert content is not None
    assert isinstance(content, str)
    assert "Example Domain" in content or "<html>" in content.lower()

@pytest.mark.asyncio
async def test_browser_manager_get_page_content_timeout(browser_manager):
    # Используем зарезервированный TEST-NET адрес (RFC 5737)
    url = "http://192.0.2.1/delay/10"
    timeout = 2
    
    with pytest.raises(Exception):
        await browser_manager.get_page_content(url, timeout_seconds=timeout)

@pytest.mark.asyncio
async def test_browser_manager_is_healthy(browser_manager):
    is_healthy_before_close = await browser_manager.is_healthy()
    assert is_healthy_before_close is True

    await browser_manager.close()
    is_healthy_after_close = await browser_manager.is_healthy()
    assert is_healthy_after_close is False
