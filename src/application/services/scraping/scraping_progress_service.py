"""
Imperative shell for scraping progress logic.

This service handles the interaction with external dependencies (repository, browser)
while delegating the core business logic to pure functions in progress_logic.py.
"""
import logging
from typing import List, Optional
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository
from src.domain.interfaces.scraping.i_progress_service import IProgressService
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.models.problem import Problem
from src.application.services.scraping.progress_logic import determine_next_page

logger = logging.getLogger(__name__)

class ScrapingProgressService(IProgressService):
    """
    Service responsible for determining scraping progress and next actions.
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
        start_page: str,
        force_restart: bool
    ) -> int:
        """
        Get the next page number to scrape for a subject.
        """
        logger.debug(f"Getting next page to scrape for subject: {subject_info.official_name}")
        
        # Get existing problems for this subject
        existing_problems = await self._repository.get_by_subject(subject_info.official_name)
        
        # Reconstruct ScrapingConfig to satisfy the functional core (determine_next_page)
        # We rely on default values for other fields not affecting page calculation.
        config = ScrapingConfig(
            start_page=start_page,
            force_restart=force_restart,
        )
        
        # Use functional core to determine next page
        next_page = determine_next_page(existing_problems, config)
        
        logger.info(f"Next page to scrape for {subject_info.official_name}: {next_page}")
        return next_page
