"""Tests for FileLinkExtractor component"""
import pytest
from bs4 import BeautifulSoup
from src.infrastructure.processors.html.components.file_link_extractor import FileLinkExtractor

class TestFileLinkExtractor:
    """Test suite for FileLinkExtractor"""
    
    @pytest.fixture
    def extractor(self):
        return FileLinkExtractor()
    
    def test_extract_no_links(self, extractor):
        """Test extraction with no file links"""
        html = "<div>No links here</div>"
        soup = BeautifulSoup(html, "html.parser")
        
        links = extractor.extract_file_links(soup)
        
        assert links == []
    
    def test_extract_pdf_links(self, extractor):
        """Test extraction of PDF links"""
        html = '<a href="document.pdf">PDF</a><a href="page.html">Regular</a>'
        soup = BeautifulSoup(html, "html.parser")
        
        links = extractor.extract_file_links(soup)
        
        assert len(links) == 1
        assert links[0][1] == "document.pdf"
    
    def test_extract_multiple_file_types(self, extractor):
        """Test extraction of multiple file types"""
        html = '''
            <a href="doc.pdf">PDF</a>
            <a href="file.doc">DOC</a>
            <a href="archive.zip">ZIP</a>
            <a href="image.jpg">JPG</a>
        '''
        soup = BeautifulSoup(html, "html.parser")
        
        links = extractor.extract_file_links(soup)
        
        assert len(links) == 3  # PDF, DOC, ZIP (no JPG)
        hrefs = [href for _, href in links]
        assert "doc.pdf" in hrefs
        assert "file.doc" in hrefs
        assert "archive.zip" in hrefs
