"""Interface for page processing in scraping use case"""
import abc
from typing import Dict, Any
from src.domain.value_objects.scraping.page_processing_result import PageProcessingResult

class IPageProcessor(abc.ABC):
    """Process individual pages during scraping"""
    
    @abc.abstractmethod
    async def process_page(
        self, 
        page_num: int, 
        subject_alias: str,
        proj_id: str,
        config_data: Dict[str, Any],
        base_run_folder: Any
    ) -> PageProcessingResult:
        pass
