"""
Imperative shell for scraping progress logic.

This service handles the interaction with external dependencies (repository, browser)
while delegating the core business logic to pure functions in progress_logic.py.
"""
import logging
from typing import List, Optional
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
from src.application.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
from src.application.services.scraping.progress_logic import determine_next_page, extract_page_number_from_url

logger = logging.getLogger(__name__)

class ScrapingProgressService:
    """
    Service responsible for determining scraping progress and next actions.
    
    This is the imperative shell that:
    1. Interacts with external dependencies (repository)
    2. Collects data needed by the functional core
    3. Applies the functional core logic
    4. Returns results to the use case
    
    It has no business logic of its own - all decisions are delegated to pure functions.
    """
    
    def __init__(self, problem_repository: IProblemRepository):
        """
        Initialize the progress service.
        
        Args:
            problem_repository: Repository to access existing problems
        """
        self._repository = problem_repository
    
    async def get_next_page_to_scrape(
        self,
        subject_info: SubjectInfo,
        config: ScrapingConfig
    ) -> int:
        """
        Get the next page number to scrape for a subject.
        
        This method handles all the imperative concerns:
        - Fetching existing problems from repository
        - Applying the functional core logic
        
        Args:
            subject_info: Subject information
            config: Scraping configuration
            
        Returns:
            Page number to start scraping from
        """
        logger.debug(f"Getting next page to scrape for subject: {subject_info.official_name}")
        
        # Get existing problems for this subject
        existing_problems = await self._repository.get_by_subject(subject_info.official_name)
        
        # Use functional core to determine next page
        next_page = determine_next_page(existing_problems, config)
        
        logger.info(f"Next page to scrape for {subject_info.official_name}: {next_page}")
        return next_page
