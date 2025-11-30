from typing import Any, Dict, List
"""Domain representation of scraping results - used by domain services"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DomainScrapingResult:
    """Domain-level representation of scraping results for internal domain use"""
    total_pages: int
    total_problems_found: int  
    total_problems_saved: int
    page_results: List[Dict[str, Any]]
    errors: List[str]
    start_time: datetime
    end_time: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    @property 
    def success_rate(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return (self.total_problems_saved / self.total_pages) * 100.0
