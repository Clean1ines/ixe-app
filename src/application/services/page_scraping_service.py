"""
Application service for page scraping operations.

This service coordinates the scraping of individual pages, handling the interaction
between browser management (via IBrowserService) and HTML processing (via IHTMLProcessor).
It converts the results into a format suitable for the domain (e.g., using IProblemFactory).
"""
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from src.domain.interfaces.external_services.i_browser_service import IBrowserService
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor
from src.application.interfaces.factories.i_problem_factory import IProblemFactory
from src.domain.models.problem import Problem

logger = logging.getLogger(__name__)

class PageScrapingService:
    """
    Application service for page scraping operations.
    
    Business Rules:
    - Coordinates the scraping of a single page
    - Uses IBrowserService to get page content
    - Uses IHTMLProcessor to process the HTML content
    - Uses IProblemFactory to convert processed data into domain entities
    - Handles errors gracefully during scraping and processing
    """
    
    def __init__(
        self,
        browser_service: IBrowserService,
        html_processor: IHTMLProcessor,
        problem_factory: IProblemFactory,
    ):
        """
        Initialize page scraping service.
        
        Args:
            browser_service: Service for browser management (implements IBrowserService)
            html_processor: Service for processing HTML blocks (implements IHTMLProcessor)
            problem_factory: Service for creating domain problems (implements IProblemFactory)
        """
        self.browser_service = browser_service
        self.html_processor = html_processor
        self.problem_factory = problem_factory

    async def scrape_page(
        self,
        url: str,
        subject: str,
        base_url: str = "https://ege.fipi.ru", # Дефолтный URL можно передавать извне или брать из конфига
        timeout: int = 30
    ) -> List[Problem]: # Теперь возвращаем List[Problem]
        """
        Scrape a single page and return Problem entities.
        
        Args:
            url: The URL of the page to scrape.
            subject: The subject name (e.g., "math", "informatics") for context.
            base_url: The base URL of the FIPI site.
            timeout: Timeout for browser operations.
            
        Returns:
            A list of Problem entities extracted from the page.
        """
        logger.info(f"Scraping page: {url} for subject: {subject}")
        
        # 1. Get page content using IBrowserService
        try:
            page_content = await self.browser_service.get_page_content(url, timeout)
        except Exception as e:
            logger.error(f"Failed to get page content from {url}: {e}")
            raise # или возвращаем пустой список/ошибку в ScrapingPageResult

        # 2. Parse HTML content
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # 3. Find problem blocks (header_container and qblock pairs)
        # This logic might be extracted to a separate helper/service if it becomes complex
        problems = []
        header_containers = soup.find_all('div', class_='task-header-panel') # Пример селектора
        qblocks = soup.find_all('div', class_='qblock') # Пример селектора
        
        if len(header_containers) != len(qblocks):
            logger.warning(f"Mismatch between header panels ({len(header_containers)}) and qblocks ({len(qblocks)}) on page {url}. Attempting pairing by index.")
        
        # Pair them based on index (this is a simplification, real logic might be more complex)
        for i, (header_container, qblock) in enumerate(zip(header_containers, qblocks)):
             # 4. Process each block using IHTMLProcessor
            try:
                processed_data = await self.html_processor.process_html_block(
                    header_container=header_container,
                    qblock=qblock,
                    block_index=i,
                    subject=subject,
                    base_url=base_url
                )
                # 5. Create Problem entity using IProblemFactory
                problem = self.problem_factory.create_problem(processed_data)
                problems.append(problem)
            except Exception as e:
                logger.error(f"Error processing block {i} on page {url}: {e}")
                # Decide whether to continue or fail the whole page based on business rules
                # For now, we continue processing other blocks
                continue
        
        logger.info(f"Scraped {len(problems)} problems from page: {url}")
        return problems

