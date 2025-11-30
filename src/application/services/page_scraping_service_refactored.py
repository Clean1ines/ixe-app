# Создаем новый файл: src/application/services/page_scraping_service_refactored.py
"""
Refactored PageScrapingService with reduced complexity.
"""

import logging
import urllib.parse
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple

from bs4 import BeautifulSoup, Tag

from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser

from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter
from src.domain.html_processing.pure_html_transforms import extract_block_pairs

logger = logging.getLogger(__name__)

class PageScrapingServiceRefactored:
    def __init__(
        self,
        browser_service: IBrowserService,
        asset_downloader_impl: IAssetDownloader,
        problem_factory: IProblemFactory,
        html_block_processing_service: HTMLBlockProcessingService,
        html_block_parser: Optional[IHTMLBlockParser] = None,
        timeout: int = None
    ):
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl
        self.problem_factory = problem_factory
        self.html_block_processing_service = html_block_processing_service
        self.html_block_parser = html_block_parser
        self.timeout = self._get_timeout(timeout)

    def _get_timeout(self, timeout: Optional[int]) -> int:
        """Get timeout from parameter or config with fallback."""
        if timeout is not None:
            return timeout
        
        try:
            from src.core.config import config
            return getattr(config.browser, 'timeout_seconds', 30)
        except ImportError:
            return 30

    def _get_base_url(self, base_url: Optional[str]) -> str:
        """Get base URL from parameter or config with fallback."""
        if base_url is not None:
            return base_url
        
        try:
            from src.core.config import config
            return getattr(config.scraping, 'base_url', 'https://fipi.ru')
        except ImportError:
            return 'https://fipi.ru'

    async def _setup_browser_page(self, browser_manager, url: str, timeout: int) -> Any:
        """Set up browser page with proper configuration."""
        logger.debug(f"Creating new page for {url} with timeout {timeout}s")
        page = await browser_manager._browser.new_page()
        
        await page.set_viewport_size({
            "width": browser_manager.default_viewport_width,
            "height": browser_manager.default_viewport_height
        })
        await page.set_extra_http_headers({
            "User-Agent": browser_manager.default_user_agent
        })
        page.set_default_timeout(timeout * 1000)
        
        return page

    async def _handle_iframe_content(self, page, url: str, timeout: int) -> Tuple[str, str]:
        """Handle iframe content extraction with fallback to main content."""
        actual_page_content = await page.content()
        actual_source_url = url

        page_soup = BeautifulSoup(actual_page_content, "html.parser")
        questions_iframe = page_soup.find('iframe', id='questions_container')

        if not questions_iframe:
            logger.debug(f"No questions iframe found on {url}.")
            return actual_page_content, actual_source_url

        iframe_src = questions_iframe.get('src')
        if not iframe_src:
            logger.warning(f"Iframe found on {url} without 'src'; using main page content.")
            return actual_page_content, actual_source_url

        full_iframe_url = urllib.parse.urljoin(url, iframe_src)
        actual_source_url = full_iframe_url
        
        try:
            await page.goto(full_iframe_url, wait_until="networkidle", timeout=timeout * 1000)
            actual_page_content = await page.content()
            logger.debug(f"Fetched iframe content ({len(actual_page_content)} chars) from {full_iframe_url}")
        except Exception as e_iframe:
            logger.error(f"Failed to get iframe content {full_iframe_url}: {e_iframe}", exc_info=True)
            logger.warning("Falling back to main page content.")
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            actual_page_content = await page.content()
            actual_source_url = url

        return actual_page_content, actual_source_url

    def _parse_html_blocks(self, html_content: str) -> List[List[Tag]]:
        """Parse HTML content into grouped blocks using available parsers."""
        if not html_content:
            return []

        try:
            if self.html_block_parser:
                return self.html_block_parser.parse_blocks(html_content)
            else:
                return self._parse_blocks_with_fallback(html_content)
        except Exception as e:
            logger.error(f"Failed to parse HTML blocks: {e}", exc_info=True)
            return []

    def _parse_blocks_with_fallback(self, html_content: str) -> List[List[Tag]]:
        """Parse blocks using pure functional core as fallback."""
        block_pairs = extract_block_pairs(html_content)
        grouped_blocks = []
        
        for header_html, body_html in block_pairs:
            header_dom = BeautifulSoup(header_html or "", "html.parser").find()
            body_dom = BeautifulSoup(body_html or "", "html.parser").find() if body_html else None
            elements = [el for el in (header_dom, body_dom) if el is not None]
            grouped_blocks.append(elements)
            
        return grouped_blocks

    def _create_processing_context(
        self, 
        subject_info: SubjectInfo,
        url: str,
        run_folder_page: Path,
        files_location_prefix: str,
        base_url: str
    ) -> Dict[str, Any]:
        """Create processing context for block processing."""
        return {
            'run_folder_page': run_folder_page,
            'asset_downloader': self.asset_downloader_impl,
            'base_url': base_url,
            'files_location_prefix': files_location_prefix,
            'subject_info': subject_info,
            'source_url': url,
        }

    async def _process_blocks(
        self, 
        grouped_blocks: List[List[Tag]], 
        context: Dict[str, Any],
        url: str
    ) -> List[Any]:
        """Process all blocks and return problems."""
        problems = []
        
        for i, block_elements in enumerate(grouped_blocks):
            try:
                problem = await self.html_block_processing_service.process_block(
                    block_elements=block_elements,
                    block_index=i,
                    context=context
                )
                if problem is not None:
                    problems.append(problem)
            except Exception as e_block:
                logger.error(f"Error processing grouped block {i} on page {url}: {e_block}", exc_info=True)
                continue
                
        return problems

    def _count_assets(self, run_folder_page: Path) -> int:
        """Count assets in the page assets directory."""
        page_assets_dir = run_folder_page / "assets"
        if page_assets_dir.exists():
            return sum(1 for _ in page_assets_dir.iterdir() if _.is_file())
        return 0

    async def scrape_page(
        self,
        url: str,
        subject_info: SubjectInfo,
        base_url: str = None,
        timeout: int = None,
        run_folder_page: Optional[Path] = None,
        files_location_prefix: str = ""
    ) -> List[Any]:
        """
        Scrape a single page and return Problem entities.
        Refactored to reduce complexity.
        """
        # Resolve configuration
        actual_base_url = self._get_base_url(base_url)
        actual_timeout = timeout or self.timeout
        actual_run_folder = run_folder_page or Path(".")

        logger.info(f"Scraping page: {url} for subject: {subject_info.official_name}")

        # Browser setup and navigation
        browser_manager = await self.browser_service.get_browser()
        try:
            page = await self._setup_browser_page(browser_manager, url, actual_timeout)
            
            logger.debug(f"Navigating page to {url}")
            await page.goto(url, wait_until="networkidle", timeout=actual_timeout * 1000)

            # Content extraction with iframe handling
            page_content, source_url = await self._handle_iframe_content(page, url, actual_timeout)

            # HTML block parsing
            grouped_blocks = self._parse_html_blocks(page_content)
            logger.debug(f"Found {len(grouped_blocks)} grouped blocks on page {url} (source {source_url}).")

            # Block processing
            context = self._create_processing_context(
                subject_info, url, actual_run_folder, files_location_prefix, actual_base_url
            )
            
            problems = await self._process_blocks(grouped_blocks, context, url)

        finally:
            await page.close()
            await self.browser_service.release_browser(browser_manager)

        # Asset counting for logging
        assets_count = self._count_assets(actual_run_folder)
        logger.debug(f"Assets saved to {actual_run_folder / 'assets'}: {assets_count}")

        return problems
