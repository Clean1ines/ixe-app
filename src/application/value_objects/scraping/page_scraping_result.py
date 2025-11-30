from dataclasses import dataclass, field
from typing import List, Optional
from src.domain.models.problem import Problem


@dataclass
class PageScrapingResult:
    """Value Object representing the result of scraping a single page."""
    
    page_url: str
    success: bool
    problems: List[Problem] = field(default_factory=list)
    error_message: Optional[str] = None
    assets_downloaded: int = 0

    def __post_init__(self):
        """Validate the scraping result."""
        if not self.page_url:
            raise ValueError("Page URL cannot be empty")
        if self.success and not self.problems:
            raise ValueError("Successful scraping must have at least one problem")
