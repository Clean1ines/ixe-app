"""Scraping interfaces"""
from .i_content_fetcher import IContentFetcher
from .i_iframe_handler import IIframeHandler

__all__ = [
    "IContentFetcher",
    "IIframeHandler",
]
