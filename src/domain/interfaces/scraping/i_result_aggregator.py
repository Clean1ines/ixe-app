"""Fixed interface for result aggregation - uses domain objects only"""
import abc
from typing import List, Dict, Any
from datetime import datetime
from src.domain.value_objects.scraping.domain_scraping_result import DomainScrapingResult

class IResultAggregator(abc.ABC):
    """Domain interface for aggregating scraping results"""
    
    @abc.abstractmethod
    def aggregate_results(
        self,
        page_results: List[Dict[str, Any]],
        total_problems_saved: int,
        total_problems_found: int,
        errors: List[str],
        start_time: datetime,
        end_time: datetime
    ) -> DomainScrapingResult:
        """Aggregate page results into final domain result"""
        pass
