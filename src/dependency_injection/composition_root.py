import asyncio
from pathlib import Path
from typing import Tuple
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.services.page_scraping_service import PageScrapingService
from src.application.services.html_block_processing_service import HTMLBlockProcessingService
from src.application.factories.problem_factory import ProblemFactory
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.infrastructure.adapters.external_services.playwright_asset_downloader_adapter import PlaywrightAssetDownloaderAdapter
from src.infrastructure.adapters.browser_pool_service_adapter import BrowserPoolServiceAdapter
from src.infrastructure.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository, Base
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover
from src.application.services.scraping.scraping_progress_service import ScrapingProgressService
from src.application.services.scraping.progress_reporter import ScrapingProgressReporter
from src.application.services.html_parsing.i_html_block_parser import IHTMLBlockParser
from src.application.services.html_parsing.fipa_page_block_parser import FIPIPageBlockParser
from src.infrastructure.adapters.html_processing.metadata_extractor_adapter import MetadataExtractorAdapter

# Импорты новой архитектуры
from src.domain.interfaces.services.i_page_scraping_service import IPageScrapingService
from src.infrastructure.services.page_scraping_adapter import PageScrapingAdapter

# Import centralized configuration
try:
    from src.core.config import config
    CENTRAL_CONFIG_AVAILABLE = True
except ImportError:
    CENTRAL_CONFIG_AVAILABLE = False
    # Create a simple fallback config
    class FallbackConfig:
        database = type('Database', (), {'url': 'sqlite:///./ege_problems.db'})()
        browser = type('Browser', (), {'timeout_seconds': 30})()
        scraping = type('Scraping', (), {'asset_download_timeout': 60})()
    config = FallbackConfig()

async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def create_scraping_components(base_run_folder: Path) -> Tuple[ScrapeSubjectUseCase, IBrowserService, IAssetDownloader]:
    # Use centralized configuration for timeouts with graceful degradation
    if CENTRAL_CONFIG_AVAILABLE:
        asset_download_timeout = getattr(config.scraping, 'asset_download_timeout', 60)
        browser_timeout = getattr(config.browser, 'timeout_seconds', 30)
        pool_size = 2  # Could be configurable in the future
    else:
        asset_download_timeout = 60
        browser_timeout = 30
        pool_size = 2

    asset_downloader_impl: IAssetDownloader = PlaywrightAssetDownloaderAdapter(timeout=asset_download_timeout)

    browser_service: IBrowserService = BrowserPoolServiceAdapter(pool_size=pool_size)

    # Use centralized configuration for database URL
    if CENTRAL_CONFIG_AVAILABLE:
        db_url = getattr(config.database, 'url', 'sqlite:///./ege_problems.db')
        db_echo = getattr(config.database, 'echo', False)
        db_pool_size = getattr(config.database, 'pool_size', 20)
        db_max_overflow = getattr(config.database, 'max_overflow', 30)
    else:
        db_url = 'sqlite:///./ege_problems.db'
        db_echo = False
        db_pool_size = 20
        db_max_overflow = 30

    db_path = base_run_folder / "fipi_data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Use configured database URL or fallback to file-based
    if db_url.startswith('sqlite:'):
        # For SQLite, use the file path
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=db_echo)
    else:
        # For other databases, use the configured URL directly
        engine = create_async_engine(db_url, echo=db_echo, pool_size=db_pool_size, max_overflow=db_max_overflow)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create tables in a separate thread to avoid the nested event loop issue
    import threading
    def run_create_tables():
        asyncio.run(create_tables(engine))

    # Run the async function in a separate thread
    thread = threading.Thread(target=run_create_tables)
    thread.start()
    thread.join()

    problem_repository: IProblemRepository = SQLAlchemyProblemRepository(session_factory)

    problem_factory: IProblemFactory = ProblemFactory()

    html_block_parser: IHTMLBlockParser = FIPIPageBlockParser()

    metadata_extractor = MetadataExtractorAdapter()

    # NEW: Inject asset_downloader_impl into ImageScriptProcessor
    image_processor = ImageScriptProcessor(asset_downloader=asset_downloader_impl)
    file_processor = FileLinkProcessor()
    task_info_processor = TaskInfoProcessor()
    input_field_remover = InputFieldRemover()
    mathml_remover = MathMLRemover()
    unwanted_element_remover = UnwantedElementRemover()

    html_block_processing_service = HTMLBlockProcessingService(
        metadata_extractor=metadata_extractor,
        raw_processors=[
            image_processor,
            file_processor,
            task_info_processor,
            input_field_remover,
            mathml_remover,
            unwanted_element_remover
        ]
    )

    progress_service = ScrapingProgressService(problem_repository=problem_repository)
    progress_reporter = ScrapingProgressReporter()

    # Use centralized configuration for page scraping service timeout
    page_scraping_service_impl = PageScrapingService(
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
        problem_factory=problem_factory,
        html_block_processing_service=html_block_processing_service,
        html_block_parser=html_block_parser,
        timeout=browser_timeout
    )

    # NEW: Wrap the existing implementation with the domain adapter
    page_scraping_service: IPageScrapingService = PageScrapingAdapter(page_scraping_service_impl)

    scrape_use_case = ScrapeSubjectUseCase(
        page_scraping_service=page_scraping_service,  # Use the domain interface
        problem_repository=problem_repository,
        problem_factory=problem_factory,
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
        progress_service=progress_service,
        progress_reporter=progress_reporter
    )

    return scrape_use_case, browser_service, asset_downloader_impl
