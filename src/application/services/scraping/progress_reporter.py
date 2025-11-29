"""
Service for reporting scraping progress to different outputs.

This service is responsible for displaying progress information to the user
without being tied to any specific output method (CLI, web UI, etc.).
"""
import sys
from typing import Optional, TextIO, Any, Dict, List, Tuple
from datetime import timedelta
from src.application.value_objects.scraping.scraping_result import ScrapingResult
from src.domain.value_objects.scraping.subject_info import SubjectInfo

class ScrapingProgressReporter:
    """
    Reporter for scraping progress that can be used with different output streams.
    
    This class has a single responsibility: formatting and displaying progress information.
    It does not contain any business logic or interact with external services directly.
    """
    
    def __init__(self, output_stream: Optional[TextIO] = None):
        """
        Initialize the progress reporter.
        
        Args:
            output_stream: Output stream to write to (defaults to stdout)
        """
        self._output = output_stream or sys.stdout
    
    def report_start(self, subject_info: SubjectInfo, config: 'ScrapingConfig') -> None:
        """
        Report the start of scraping process.
        
        Args:
            subject_info: Subject being scraped
            config: Scraping configuration
        """
        print(f"Starting scraping for subject: {subject_info.official_name}", file=self._output)
        print(f"Configuration: mode={config.mode.name}, force_restart={config.force_restart}", file=self._output)
        if config.start_page:
            print(f"Starting from page: {config.start_page}", file=self._output)
        if config.max_pages:
            print(f"Maximum pages: {config.max_pages}", file=self._output)
        print("-" * 50, file=self._output)
    
    def report_page_progress(
        self,
        page_num: int,
        total_pages: Optional[int],
        problems_found: int,
        problems_saved: int,
        assets_downloaded: int,
        duration_seconds: float
    ) -> None:
        """
        Report progress for a single page.
        
        Args:
            page_num: Current page number
            total_pages: Total pages to process (if known)
            problems_found: Number of problems found on the page
            problems_saved: Number of problems successfully saved
            assets_downloaded: Number of assets (images/files) downloaded
            duration_seconds: Time taken to process the page
        """
        if total_pages:
            progress = f"Page {page_num}/{total_pages}"
        else:
            progress = f"Page {page_num}"
            
        print(
            f"{progress}: {problems_found} found, {problems_saved} saved, "
            f"{assets_downloaded} assets, took {duration_seconds:.2f}s",
            file=self._output
        )
    
    def report_page_error(self, page_num: int, error: str) -> None:
        """
        Report an error that occurred while processing a page.
        
        Args:
            page_num: Page number where error occurred
            error: Error message
        """
        print(f"ERROR on page {page_num}: {error}", file=self._output)
    
    def report_summary(self, result: ScrapingResult) -> None:
        """
        Report the final summary of the scraping process.
        
        Args:
            result: Final scraping result containing statistics
        """
        print("\n" + "=" * 50, file=self._output)
        print(f"Scraping Summary for {result.subject_name}", file=self._output)
        print(f"Total pages processed: {result.total_pages}", file=self._output)
        print(f"Total problems found: {result.total_problems_found}", file=self._output)
        print(f"Total problems saved: {result.total_problems_saved}", file=self._output)
        
        # Calculate assets total from page results
        total_assets = sum(
            page.get('assets_downloaded', 0) 
            for page in result.page_results
        )
        print(f"Total assets downloaded: {total_assets}", file=self._output)
        
        duration = result.end_time - result.start_time
        print(f"Total duration: {duration.total_seconds():.2f}s", file=self._output)
        
        if result.errors:
            print(f"Errors encountered: {len(result.errors)}", file=self._output)
            for i, error in enumerate(result.errors[:3], 1):  # Show first 3 errors
                print(f"  {i}. {error}", file=self._output)
            if len(result.errors) > 3:
                print(f"  ... and {len(result.errors) - 3} more", file=self._output)
        
        print("=" * 50, file=self._output)
