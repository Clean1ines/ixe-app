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

def create_scraping_components(base_run_folder: Path) -> Tuple[ScrapeSubjectUseCase, IBrowserService, IAssetDownloader]:
    asset_downloader_impl: IAssetDownloader = PlaywrightAssetDownloaderAdapter(timeout=30)

    browser_service: IBrowserService = BrowserPoolServiceAdapter(pool_size=2)

    db_path = base_run_folder / "fipi_data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    problem_repository: IProblemRepository = SQLAlchemyProblemRepository(session_factory)

    problem_factory: IProblemFactory = ProblemFactory()

    html_block_parser: IHTMLBlockParser = FIPIPageBlockParser()
    
    metadata_extractor = MetadataExtractorAdapter()

    image_processor = ImageScriptProcessor()
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

    page_scraping_service = PageScrapingService(
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
        problem_factory=problem_factory,
        html_block_processing_service=html_block_processing_service,
        html_block_parser=html_block_parser,
    )

    scrape_use_case = ScrapeSubjectUseCase(
        page_scraping_service=page_scraping_service,
        problem_repository=problem_repository,
        problem_factory=problem_factory,
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
        progress_service=progress_service,
        progress_reporter=progress_reporter
    )

    return scrape_use_case, browser_service, asset_downloader_impl
