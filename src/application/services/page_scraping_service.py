"""
Application service for page scraping operations.

Refactor notes:
- Prefer injected html_block_parser if provided (preserves existing behavior).
- If no parser is provided, fall back to pure functional core from
  src.domain.html_processing.pure_html_transforms which returns pairs of HTML strings.
- For compatibility with HTMLBlockProcessingService (which expects Tag objects),
  we re-parse those HTML fragments into BeautifulSoup Tag objects and pass them
  as grouped element lists.
- No change to external behaviour of the method (iframe handling etc. preserved).

Updated to use centralized configuration for timeouts and base URLs.
"""
import logging
import urllib.parse
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple

from bs4 import BeautifulSoup, Tag

from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser

from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter

# Import pure core fallbacks
from src.domain.html_processing.pure_html_transforms import (
    extract_block_pairs,
)

logger = logging.getLogger(__name__)

class PageScrapingService:
    def __init__(
        self,
        browser_service: IBrowserService,
        asset_downloader_impl: IAssetDownloader,
        problem_factory: IProblemFactory,
        html_block_processing_service: HTMLBlockProcessingService,
        html_block_parser: Optional[IHTMLBlockParser] = None,
        timeout: int = None
    ):
        """
        html_block_parser: optional. If provided, used to group DOM elements into blocks.
        If not provided, fallback to pure core extract_block_pairs(html) which returns
        list[(header_html, body_html)] and we convert each pair into [header_tag, body_tag].
        """
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl
        self.problem_factory = problem_factory
        self.html_block_processing_service = html_block_processing_service
        self.html_block_parser = html_block_parser
        
        # Use centralized configuration for timeout with graceful degradation
        if timeout is not None:
            self.timeout = timeout
        else:
            try:
                from src.core.config import config
                self.timeout = getattr(config.browser, 'timeout_seconds', 30)
            except ImportError:
                self.timeout = 30  # Fallback to hardcoded default

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
        
        Uses centralized configuration for base_url and timeout with graceful degradation.
        """
        # Use provided base_url or get from centralized config
        if base_url is None:
            try:
                from src.core.config import config
                base_url = getattr(config.scraping, 'base_url', 'https://fipi.ru')
            except ImportError:
                base_url = 'https://fipi.ru'  # Fallback to hardcoded default
        
        # Use provided timeout or instance timeout
        actual_timeout = timeout or self.timeout
        
        logger.info(f"Scraping page: {url} for subject: {subject_info.official_name}")
        if run_folder_page is None:
            run_folder_page = Path(".")

        asset_downloader_adapter_instance = AssetDownloaderAdapter(
            asset_downloader_impl=self.asset_downloader_impl,
            default_assets_dir=run_folder_page / "assets"
        )

        # 1) fetch main page
        try:
            page_content = await self.browser_service.get_page_content(url, actual_timeout)
        except Exception as e:
            logger.error(f"Failed to get page content from {url}: {e}", exc_info=True)
            raise

        # 2) iframe handling (preserve existing behaviour)
        page_soup = BeautifulSoup(page_content or "", "html.parser")
        questions_iframe = page_soup.find('iframe', id='questions_container')
        actual_page_content = page_content
        actual_source_url = url

        if questions_iframe:
            iframe_src = questions_iframe.get('src')
            if iframe_src:
                full_iframe_url = urllib.parse.urljoin(url, iframe_src)
                actual_source_url = full_iframe_url
                try:
                    actual_page_content = await self.browser_service.get_page_content(full_iframe_url, actual_timeout)
                    logger.debug(f"Fetched iframe content ({len(actual_page_content or '')} chars) from {full_iframe_url}")
                except Exception as e_iframe:
                    logger.error(f"Failed to get iframe content {full_iframe_url}: {e_iframe}", exc_info=True)
                    logger.warning("Falling back to main page content.")
                    actual_page_content = page_content
                    actual_source_url = url
            else:
                logger.warning(f"Iframe found on {url} without 'src'; using main page content.")
        else:
            logger.debug(f"No questions iframe found on {url}.")

        # 3) parse grouped blocks: prefer injected parser, else fallback to pure core
        grouped_blocks = []
        try:
            if self.html_block_parser:
                grouped_blocks = self.html_block_parser.parse_blocks(actual_page_content)
            else:
                # fallback: pure core returns list[(header_html, body_html)]
                block_pairs = extract_block_pairs(actual_page_content or "")
                # convert each pair into [header_tag, body_tag] (best-effort)
                for header_html, body_html in block_pairs:
                    header_dom = BeautifulSoup(header_html or "", "html.parser").find()
                    body_dom = BeautifulSoup(body_html or "", "html.parser").find() if body_html else None
                    elements = [el for el in (header_dom, body_dom) if el is not None]
                    grouped_blocks.append(elements)
        except Exception as e:
            logger.error(f"Failed to parse HTML blocks on page {url} (source {actual_source_url}): {e}", exc_info=True)
            # Return empty list instead of raising to allow partial success
            return []

        logger.debug(f"Found {len(grouped_blocks)} grouped blocks on page {url} (source {actual_source_url}).")

        problems = []
        for i, block_elements in enumerate(grouped_blocks):
            try:
                processing_context = {
                    'run_folder_page': run_folder_page,
                    'downloader': asset_downloader_adapter_instance,
                    'base_url': base_url,
                    'files_location_prefix': files_location_prefix,
                    'subject_info': subject_info,
                    'source_url': actual_source_url,
                }
                problem = await self.html_block_processing_service.process_block(
                    block_elements=block_elements,
                    block_index=i,
                    context=processing_context
                )
                if problem is not None:
                    problems.append(problem)
            except Exception as e_block:
                logger.error(f"Error processing grouped block {i} on page {url}: {e_block}", exc_info=True)
                continue

        logger.info(f"Scraped {len(problems)} problems from page: {url} (content from {actual_source_url})")
        return problems
