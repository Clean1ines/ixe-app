"""FileLinkExtractor implementation"""
from typing import List, Tuple
from bs4 import BeautifulSoup, Tag
from src.domain.interfaces.html_processing.i_file_link_extractor import IFileLinkExtractor

class FileLinkExtractor(IFileLinkExtractor):
    """Extracts file links from HTML content"""
    
    def extract_file_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """
        Extract file links from BeautifulSoup object
        """
        file_extensions = ('.pdf', '.doc', '.docx', '.zip', '.rar')
        link_tags = soup.find_all("a", href=True)
        
        file_links = []
        for link in link_tags:
            href = link.get('href', '').lower()
            if any(href.endswith(ext) for ext in file_extensions) or 'file' in (link.get('class') or []):
                file_links.append((link, href))
        
        return file_links
