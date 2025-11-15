"""
CLI handler for scraping operations.
This module provides the command-line interface for triggering the scraping process.
It acts as the composition root, assembling all necessary dependencies
and executing the ScrapeSubjectUseCase.
"""
import asyncio
import logging
import argparse
from pathlib import Path
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
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.subject_info import SubjectInfo
# Импортируем конкретные процессоры для создания списка IHTMLProcessor
from src.infrastructure.processors.html.image_script_processor import ImageScriptProcessor
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor
from src.infrastructure.processors.html.input_field_remover import InputFieldRemover
from src.infrastructure.processors.html.mathml_remover import MathMLRemover
from src.infrastructure.processors.html.unwanted_element_remover import UnwantedElementRemover

logger = logging.getLogger(__name__)

class ScrapingCLIHandler:
    """
    CLI handler for scraping operations.
    Orchestrates the dependency injection and execution of the scraping use case.
    """
    def __init__(self, base_run_folder: Path = Path("data")):
        """
        Initialize the CLI handler with a base folder for runs.
        Args:
            base_run_folder: Base path where scraping runs store their data and assets.
        """
        self.base_run_folder = base_run_folder

    async def run_scraping(self, subject_alias: str, mode: str = "full", start_page: Optional[int] = None, end_page: Optional[int] = None, force_restart: bool = False):
        """
        Run the scraping process for a given subject.
        Args:
            subject_alias: Alias of the subject to scrape (e.g., 'math', 'informatics').
            mode: Scraping mode ('full', 'update', 'range').
            start_page: Starting page number for 'range' or 'update' mode.
            end_page: Ending page number for 'range' mode.
            force_restart: If True, existing problems are updated.
        """
        logger.info(f"CLI Handler: Starting scraping for subject '{subject_alias}' in mode '{mode}'.")

        try:
            # --- 1. CREATE DEPENDENCIES ---
            # 1a. Infrastructure: Asset Downloader
            asset_downloader_impl = PlaywrightAssetDownloaderAdapter(timeout=30)
            await asset_downloader_impl.initialize()

            # 1b. Infrastructure: Browser Service
            browser_service: IBrowserService = BrowserPoolServiceAdapter(pool_size=2) # Example pool size
            await browser_service.initialize()

            # 1c. Infrastructure: Problem Repository
            # Assuming a shared database path for all subjects
            db_path = self.base_run_folder / "fipi_data.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            session_factory = SQLAlchemyProblemRepository.create_session_factory(db_path)
            problem_repository: IProblemRepository = SQLAlchemyProblemRepository(session_factory)

            # 1d. Application: Problem Factory
            problem_factory: IProblemFactory = ProblemFactory()

            # 1e. Infrastructure: Create concrete HTML processors
            # These implement IHTMLProcessor
            image_processor = ImageScriptProcessor()
            file_processor = FileLinkProcessor()
            task_info_processor = TaskInfoProcessor()
            input_field_remover = InputFieldRemover()
            mathml_remover = MathMLRemover()
            unwanted_element_remover = UnwantedElementRemover()

            # 1f. Application: Create list of IHTMLProcessor implementations
            html_processors = [
                mathml_remover,
                unwanted_element_remover,
                image_processor,
                file_processor,
                task_info_processor,
                input_field_remover,
            ]

            # 1g. Application: Create HTMLBlockProcessingService with the list of processors
            html_block_processing_service = HTMLBlockProcessingService(
                asset_downloader_impl=asset_downloader_impl,
                problem_factory=problem_factory,
                html_processors=html_processors, # Pass the list of IHTMLProcessor
            )

            # 1h. Application: Create PageScrapingService with HTMLBlockProcessingService
            page_scraping_service = PageScrapingService(
                browser_service=browser_service,
                asset_downloader_impl=asset_downloader_impl,
                problem_factory=problem_factory,
                html_block_processing_service=html_block_processing_service, # Pass the HTMLBlockProcessingService
            )

            # 1i. Application: Create Use Case
            scrape_use_case = ScrapeSubjectUseCase(
                page_scraping_service=page_scraping_service,
                problem_repository=problem_repository,
                problem_factory=problem_factory,
                browser_service=browser_service,
                asset_downloader_impl=asset_downloader_impl,
            )

            # --- 2. PREPARE INPUT DATA ---
            # Get subject info based on alias
            try:
                subject_info = SubjectInfo.from_alias(subject_alias)
            except ValueError as e:
                logger.error(f"Unknown subject alias: {subject_alias}")
                return

            # Prepare scraping config
            config = ScrapingConfig(
                mode=mode,
                base_run_folder=self.base_run_folder,
                timeout=30,
                force_restart=force_restart,
                start_page=start_page,
                end_page=end_page,
            )

            # --- 3. EXECUTE USE CASE ---
            result = await scrape_use_case.execute(subject_info, config)

            # --- 4. REPORT RESULTS ---
            logger.info(f"CLI Handler: Scraping completed for '{subject_alias}'. Result: {result}")

        except Exception as e:
            logger.error(f"CLI Handler: Error during scraping for '{subject_alias}': {e}", exc_info=True)
        finally:
            # --- 5. CLEANUP RESOURCES ---
            # Close browser service
            try:
                await browser_service.close()
            except Exception as e:
                logger.error(f"Error closing browser service: {e}")
            # Close asset downloader
            try:
                await asset_downloader_impl.close()
            except Exception as e:
                logger.error(f"Error closing asset downloader: {e}")

def main():
    """
    Main entry point for the CLI handler.
    Parses arguments and runs the scraping process.
    """
    parser = argparse.ArgumentParser(description="Scrape EGE problems from FIPI website.")
    parser.add_argument("subject", help="Subject alias to scrape (e.g., math, informatics)")
    parser.add_argument("--mode", choices=["full", "update", "range"], default="full", help="Scraping mode")
    parser.add_argument("--start-page", type=int, help="Start page for 'range' or 'update' mode")
    parser.add_argument("--end-page", type=int, help="End page for 'range' mode")
    parser.add_argument("--force-restart", action="store_true", help="Force restart (update existing problems)")
    parser.add_argument("--run-folder", type=Path, default=Path("data"), help="Base folder for run data and assets")

    args = parser.parse_args()

    handler = ScrapingCLIHandler(base_run_folder=args.run_folder)

    # Run the async function
    asyncio.run(handler.run_scraping(
        subject_alias=args.subject,
        mode=args.mode,
        start_page=args.start_page,
        end_page=args.end_page,
        force_restart=args.force_restart
    ))

if __name__ == "__main__":
    main()
