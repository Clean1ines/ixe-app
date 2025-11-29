"""Fake browser page implementation for testing"""
from unittest.mock import AsyncMock
from typing import Dict, Optional


class FakeBrowserPage:
    """Fake implementation of a browser page for testing iframe handling"""
    
    def __init__(self):
        self._current_url = None
        self._content_map: Dict[str, str] = {}
        self._goto_calls = []
        self._content_calls = []
        
    async def goto(self, url: str, wait_until: str = "networkidle", timeout: int = 30000):
        """Navigate to URL - fake implementation"""
        self._goto_calls.append({
            'url': url,
            'wait_until': wait_until,
            'timeout': timeout
        })
        
        if url in self._content_map:
            self._current_url = url
        else:
            # Simulate navigation error for URLs not in content map
            raise Exception(f"Navigation failed to {url}")
            
    async def content(self) -> str:
        """Get page content - fake implementation"""
        self._content_calls.append(self._current_url)
        
        if self._current_url in self._content_map:
            return self._content_map[self._current_url]
        return "<html>Default content</html>"
    
    def set_content_for_url(self, url: str, content: str):
        """Setup content for specific URL"""
        self._content_map[url] = content
        
    def get_goto_calls(self) -> list:
        """Get all goto calls for verification"""
        return self._goto_calls.copy()
        
    def get_content_calls(self) -> list:
        """Get all content calls for verification"""
        return self._content_calls.copy()
    
    def set_current_url(self, url: str):
        """Set current URL for testing"""
        self._current_url = url
