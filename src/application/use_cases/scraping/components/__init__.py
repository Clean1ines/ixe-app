"""Components for scraping use cases."""
from .data_structures import PageResult, LoopResult
from .page_processor import PageProcessor
from .scraping_loop_controller import ScrapingLoopController
from .result_composer import ResultComposer

__all__ = [
    'PageResult',
    'LoopResult', 
    'PageProcessor',
    'ScrapingLoopController',
    'ResultComposer'
]
