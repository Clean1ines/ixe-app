from dataclasses import dataclass
from typing import List
from src.domain.models.problem import Problem


@dataclass
class PageScrapingResult:
    problems: List[Problem]
    assets_downloaded: int

    def __init__(self, problems: List[Problem] = None, assets_downloaded: int = 0):
        self.problems = problems or []
        self.assets_downloaded = assets_downloaded
