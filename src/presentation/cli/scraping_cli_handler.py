"""
CLI handler for scraping operations.
This module provides the command-line interface for triggering the scraping process.
It depends only on the abstract ScrapeSubjectUseCase and receives its dependencies
via the main function, adhering to DIP.
"""
import asyncio
import logging
import argparse
import urllib.parse # ИМПОРТИРУЕМ urllib.parse В НАЧАЛЕ ФАЙЛА
from pathlib import Path
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader
from src.dependency_injection.composition_root import create_scraping_components
from src.application.services.scraping.progress_reporter import ScrapingProgressReporter

logger = logging.getLogger(__name__)

class ScrapingCLIHandler:
    """
    CLI handler for scraping operations.
    Depends only on the ScrapeSubjectUseCase abstraction.
    """
    def __init__(self, scrape_use_case: ScrapeSubjectUseCase):
        """
        Initialize the CLI handler with the use case it will execute.
        Args:
            scrape_use_case: The use case for scraping a single subject.
        """
        self.scrape_use_case = scrape_use_case

    async def run_scraping(self, subject_alias: str, mode: str = "full", start_page: int = None, end_page: int = None, force_restart: bool = False, base_run_folder: Path = Path("data")):
        """
        Run the scraping process for a given subject.
        Args:
            subject_alias: Alias of the subject to scrape (e.g., 'math', 'informatics').
            mode: Scraping mode ('full', 'update', 'range').
            start_page: Starting page number for 'range' or 'update' mode.
            end_page: Ending page number for 'range' mode.
            force_restart: If True, existing problems are updated.
            base_run_folder: Base path for run data and assets.
        """
        logger.info(f"CLI Handler: Starting scraping for subject '{subject_alias}' in mode '{mode}'.")

        try:
            # Get subject info based on alias
            try:
                subject_info = SubjectInfo.from_alias(subject_alias)
            except ValueError as e:
                logger.error(f"Unknown subject alias: {subject_alias}")
                print(f"Error: Unknown subject alias: {subject_alias}")
                return

            # Map string mode to ScrapingMode enum
            mode_enum = ScrapingMode.SEQUENTIAL
            if mode == "range":
                mode_enum = ScrapingMode.SEQUENTIAL
            elif mode == "full":
                mode_enum = ScrapingMode.SEQUENTIAL

            # Prepare scraping config
            config = ScrapingConfig(
                mode=mode_enum,
                timeout_seconds=30,
                force_restart=force_restart,
                start_page=start_page,
                max_pages=end_page,
            )

            # Execute use case - it will handle all progress reporting internally
            result = await self.scrape_use_case.execute(subject_info, config)

            # Final result reporting is handled by the progress reporter in the use case
            if not result.success:
                print(f"Scraping completed with errors. Check logs for details.")
            else:
                print(f"Scraping completed successfully!")

        except Exception as e:
            logger.error(f"CLI Handler: Error during scraping for '{subject_alias}': {e}", exc_info=True)
            print(f"Error during scraping: {e}")
            raise # Re-raise to be handled by main for cleanup


def main():
    """
    Main entry point for the CLI handler.
    Parses arguments, creates dependencies via composition_root, and runs the scraping process.
    """
    parser = argparse.ArgumentParser(description="Scrape EGE problems from FIPI website.")
    parser.add_argument("subject", help="Subject alias to scrape (e.g., math, informatics)")
    parser.add_argument("--mode", choices=["full", "update", "range"], default="full", help="Scraping mode")
    parser.add_argument("--start-page", type=int, help="Start page for 'range' or 'update' mode")
    parser.add_argument("--end-page", type=int, help="End page for 'range' mode")
    parser.add_argument("--force-restart", action="store_true", help="Force restart (update existing problems)")
    parser.add_argument("--run-folder", type=Path, default=Path("data"), help="Base folder for run data and assets")

    args = parser.parse_args()

    print(f"Subject: {args.subject}")
    print(f"Mode: {args.mode}")
    print(f"Start page: {args.start_page}")
    print(f"End page: {args.end_page}")
    print(f"Force restart: {args.force_restart}")
    print(f"Run folder: {args.run_folder}")
    
    # Create components
    scrape_use_case, browser_service, asset_downloader_impl = create_scraping_components(base_run_folder=args.run_folder)

    handler = ScrapingCLIHandler(scrape_use_case=scrape_use_case)

    async def run_with_cleanup():
        try:
            await asset_downloader_impl.initialize()
            await browser_service.initialize()
            await handler.run_scraping(
                subject_alias=args.subject,
                mode=args.mode,
                start_page=args.start_page,
                end_page=args.end_page,
                force_restart=args.force_restart,
                base_run_folder=args.run_folder
            )
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}", exc_info=True)
            print(f"Critical error: {e}")
            raise        
        finally:
            # Cleanup resources
            try:
                await browser_service.close()
            except Exception as e:
                logger.error(f"Error closing browser service: {e}")
            try:
                await asset_downloader_impl.close()
            except Exception as e:
                logger.error(f"Error closing asset downloader: {e}")

    # Run the async function with cleanup
    asyncio.run(run_with_cleanup())

if __name__ == "__main__":
    main()
