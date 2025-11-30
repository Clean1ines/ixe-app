from typing import Any, Dict, List, Optional, Tuple
"""
Application service for page scraping operations.

Refactored to use dedicated components for each responsibility.
"""
import logging
from pathlib import Path

from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser

# Import components
from src.infrastructure.services.page_scraping.components.iframe_handler import IframeHandler
from src.infrastructure.services.page_scraping.components.content_fetcher import ContentFetcher
from src.infrastructure.services.page_scraping.components.block_parser import BlockParser

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
        Initialize with dependencies and setup components.
        """
        self.browser_service = browser_service
        self.asset_downloader_impl = asset_downloader_impl
        self.problem_factory = problem_factory
        self.html_block_processing_service = html_block_processing_service
        self.html_block_parser = html_block_parser

        # Setup components
        self.content_fetcher = ContentFetcher(browser_service)
        self.iframe_handler = IframeHandler()
        self.block_parser = BlockParser(html_block_parser)

        # Use centralized configuration for timeout with graceful degradation
        if timeout is not None:
            self.timeout = timeout
        else:
            try:
                from src.core.config import config
                self.timeout = getattr(config.browser, 'timeout_seconds', 30)
            except ImportError:
                self.timeout = 30

    def _get_base_url(self, base_url: Optional[str]) -> str:
        """Get base URL from parameter or config with fallback."""
        if base_url is not None:
            return base_url

        try:
            from src.core.config import config
            return getattr(config.scraping, 'base_url', 'https://fipi.ru')
        except ImportError:
            return 'https://fipi.ru'

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
        grouped_blocks: List, 
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
            # Мы подсчитываем именно количество файлов в папке, чтобы получить 1 ассет, а не 10.
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
    ) -> Tuple[List[Any], int]:
        """
        Scrape a single page and return Problem entities and the count of downloaded assets 
        (counted via filesystem due to asset_downloader caching logic).
        """
        # Resolve configuration
        actual_base_url = self._get_base_url(base_url)
        actual_timeout = timeout or self.timeout
        actual_run_folder = run_folder_page or Path(".")

        assets_count = 0

        logger.info(f"Scraping page: {url} for subject: {subject_info.official_name}")

        try:
            # 1. Fetch page content using ContentFetcher
            page_content, source_url = await self.content_fetcher.fetch_page_content(url, actual_timeout)

            # 2. Handle iframe content using IframeHandler
            page = await self.content_fetcher.get_page()
            page_content, source_url = await self.iframe_handler.handle_iframe_content(
                page, url, actual_timeout, page_content
            )

            # 3. Parse HTML blocks using BlockParser
            grouped_blocks = self.block_parser.parse_html_blocks(page_content)
            logger.debug(f"Found {len(grouped_blocks)} grouped blocks on page {url} (source {source_url}).")

            # 4. Process blocks through HTMLBlockProcessingService
            context = self._create_processing_context(
                subject_info, url, actual_run_folder, files_location_prefix, actual_base_url
            )

            problems = await self._process_blocks(grouped_blocks, context, url)

            # 5. Count assets (Filesystem counting restores functional reporting)
            assets_count = self._count_assets(actual_run_folder)
            logger.debug(f"Assets saved to {actual_run_folder / 'assets'}: {assets_count}")

            # Возвращаем проблемы И количество ассетов (кортеж из двух)
            return problems, assets_count

        except Exception as e:
            logger.error(f"Failed to scrape page {url}: {e}", exc_info=True)
            # ВОЗВРАЩАЕМ КОРТЕЖ ИЗ ДВУХ ЭЛЕМЕНТОВ, чтобы избежать ValueError в адаптере
            return [], 0
        finally:
            # Ensure browser resources are cleaned up
            await self.content_fetcher.cleanup_browser()
