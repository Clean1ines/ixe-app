"""
Application service for orchestrating parallel scraping of multiple subjects.
This service takes a list of subjects and their configurations,
and executes the ScrapeSubjectUseCase for each one concurrently.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from src.application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.scraping_result import ScrapingResult

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """
    Application service for orchestrating parallel scraping of multiple subjects.
    Business Rules:
    - Accepts a list of subject aliases and configurations
    - Executes ScrapeSubjectUseCase for each subject concurrently using asyncio.gather
    - Aggregates results from all subjects
    - Handles errors gracefully at the subject level
    - Provides overall progress and summary
    """
    def __init__(self, scrape_use_case: ScrapeSubjectUseCase):
        """
        Initialize the orchestrator with the use case it will execute.
        Args:
            scrape_use_case: The use case for scraping a single subject.
        """
        self.scrape_use_case = scrape_use_case

    async def run_parallel_scraping(
        self,
        subject_configs: List[Dict[str, Any]] # List of dicts like {"subject_alias": "...", "config": ScrapingConfig}
    ) -> Dict[str, ScrapingResult]:
        """
        Run scraping for multiple subjects in parallel.
        Args:
            subject_configs: A list of dictionaries, each containing:
                             - "subject_alias": The alias of the subject (e.g., "math", "informatics")
                             - "config": An instance of ScrapingConfig for that subject
                             - Optional: Any other parameters ScrapeSubjectUseCase.execute() needs
        Returns:
            A dictionary mapping subject aliases to their individual ScrapingResult.
        """
        logger.info(f"Starting parallel scraping for {len(subject_configs)} subjects.")
        
        # Prepare tasks for asyncio.gather
        tasks = []
        for item in subject_configs:
            subject_alias = item["subject_alias"]
            config = item["config"]
            # Create an async task for each subject's scraping
            task = asyncio.create_task(
                self._scrape_single_subject(subject_alias, config),
                name=f"Scrape_{subject_alias}"
            )
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and map them back to subject aliases
        final_results = {}
        for i, item in enumerate(subject_configs):
            subject_alias = item["subject_alias"]
            result_or_exception = results[i]
            
            if isinstance(result_or_exception, Exception):
                logger.error(f"Scraping failed for subject '{subject_alias}' with exception: {result_or_exception}", exc_info=True)
                # Create an error result using the correct ScrapingResult constructor
                final_results[subject_alias] = ScrapingResult(
                    subject_name=subject_alias, # Use alias or a placeholder
                    success=False,
                    total_pages=0,
                    total_problems_found=0,
                    total_problems_saved=0,
                    page_results=[],
                    errors=[str(result_or_exception)],
                    start_time=datetime.now(), # Use current time
                    end_time=datetime.now()  # Use current time
                )
            else:
                # It's a ScrapingResult
                final_results[subject_alias] = result_or_exception

        logger.info(f"Completed parallel scraping for {len(subject_configs)} subjects.")
        return final_results

    async def _scrape_single_subject(self, subject_alias: str, config: ScrapingConfig) -> ScrapingResult:
        """
        Helper method to scrape a single subject and return its result.
        This is wrapped in a task by run_parallel_scraping.
        """
        logger.debug(f"Orchestrator starting scrape task for subject '{subject_alias}' with config {config}.")
        try:
            # Get subject info based on alias
            subject_info = SubjectInfo.from_alias(subject_alias)
            # Execute the use case
            result = await self.scrape_use_case.execute(subject_info, config)
            logger.debug(f"Orchestrator completed scrape task for subject '{subject_alias}'. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Orchestrator error in _scrape_single_subject for '{subject_alias}': {e}", exc_info=True)
            # Re-raise to be caught by asyncio.gather as an exception result
            raise
