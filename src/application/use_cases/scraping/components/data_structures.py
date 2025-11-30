from typing import List, Optional
from dataclasses import dataclass


@dataclass
class PageResult:
    page_number: int
    problems_found: int
    problems_saved: int
    assets_downloaded: int
    page_duration_seconds: float
    error: Optional[str] = None


@dataclass
class LoopResult:
    page_results: List[PageResult]
    total_problems_found: int
    total_problems_saved: int
    total_assets_downloaded: int
    errors: List[str]
    last_processed_page: int
