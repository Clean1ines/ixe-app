from dataclasses import dataclass
from typing import List
from src.domain.models.problem import Problem


@dataclass(frozen=True)
class PageScrapingResult:
    """Value Object representing the result of scraping a single page."""
    problems: List[Problem]
    assets_downloaded: int

    def __post_init__(self):
        if not isinstance(self.problems, list):
            raise ValueError("Problems must be a list")
        if not isinstance(self.assets_downloaded, int) or self.assets_downloaded < 0:
            raise ValueError("Assets downloaded must be a non-negative integer")
