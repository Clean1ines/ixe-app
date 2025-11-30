from typing import Any, Dict, List, Optional
"""
Value Object representing the result of a scraping operation.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass  # Убираем frozen=True
class ScrapingResult:
    """
    Value Object for scraping process results and statistics.
    """
    subject_name: str
    success: bool
    total_pages: int
    total_problems_found: int
    total_problems_saved: int
    page_results: List[Dict[str, Any]]  # List of results per page
    errors: List[str]
    start_time: datetime
    end_time: datetime
    metadata: Optional[Dict[str, Any]] = None  # Optional additional data

    @property
    def duration_seconds(self) -> float:
        """Get duration of scraping in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_pages == 0:
            return 0.0
        return (self.total_problems_saved / self.total_pages) * 100.0
