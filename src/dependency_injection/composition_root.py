"""
Composition Root module for assembling application dependencies.

This module provides functions to create the complete object graph
for the application, adhering to DIP by injecting concrete implementations
into abstract interfaces. It centralizes the configuration and instantiation
logic, separating it from the CLI handler and other presentation logic.
"""
import asyncio
from pathlib import Path
from typing import Tuple
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
from src.infrastructure.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover

def create_scraping_components(base_run_folder: Path) -> Tuple[ScrapeSubjectUseCase, IBrowserService, IAssetDownloader]:
    """
    Creates and wires together all components needed for scraping.

    Args:
        base_run_folder: Base path where scraping runs store their data and assets.

    Returns:
        A tuple containing:
        - ScrapeSubjectUseCase: The main use case.
        - IBrowserService: The browser service (needs manual initialization/cleanup).
        - IAssetDownloader: The asset downloader (needs manual initialization/cleanup).
    """
    # 1. Infrastructure: Asset Downloader
    asset_downloader_impl: IAssetDownloader = PlaywrightAssetDownloaderAdapter(timeout=30)

    # 2. Infrastructure: Browser Service
    browser_service: IBrowserService = BrowserPoolServiceAdapter(pool_size=2)

    # 3. Infrastructure: Problem Repository
    db_path = base_run_folder / "fipi_data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    session_factory = SQLAlchemyProblemRepository.create_session_factory(db_path)
    problem_repository: IProblemRepository = SQLAlchemyProblemRepository(session_factory)

    # 4. Application: Problem Factory
    problem_factory: IProblemFactory = ProblemFactory()

    # 5. Infrastructure: Create concrete HTML processors (IHTMLProcessor implementations)
    image_processor = ImageScriptProcessor()
    file_processor = FileLinkProcessor()
    task_info_processor = TaskInfoProcessor()
    input_field_remover = InputFieldRemover()
    mathml_remover = MathMLRemover()
    unwanted_element_remover = UnwantedElementRemover()

    # 6. Application: Create list of IHTMLProcessor implementations
    html_processors = [
        mathml_remover,
        unwanted_element_remover,
        image_processor,
        file_processor,
        task_info_processor,
        input_field_remover,
    ]

    # 7. Application: Create HTMLBlockProcessingService with the list of processors
    html_block_processing_service = HTMLBlockProcessingService(
        asset_downloader_impl=asset_downloader_impl,
        problem_factory=problem_factory,
        html_processors=html_processors,
    )

    # 8. Application: Create PageScrapingService with HTMLBlockProcessingService
    page_scraping_service = PageScrapingService(
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
        problem_factory=problem_factory,
        html_block_processing_service=html_block_processing_service,
    )

    # 9. Application: Create Use Case
    scrape_use_case = ScrapeSubjectUseCase(
        page_scraping_service=page_scraping_service,
        problem_repository=problem_repository,
        problem_factory=problem_factory,
        browser_service=browser_service,
        asset_downloader_impl=asset_downloader_impl,
    )

    return scrape_use_case, browser_service, asset_downloader_impl
