"""Domain value object for page processing results"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class PageProcessingResult:
    """Domain representation of page processing result"""
    page_number: int
    problems_found: int
    problems_saved: int
    assets_downloaded: int
    page_duration_seconds: float
    error: Optional[str] = None
