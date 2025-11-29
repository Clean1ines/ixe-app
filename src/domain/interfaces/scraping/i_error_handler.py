"""Interface for error handling in scraping use case"""
import abc
from typing import List

class IErrorHandler(abc.ABC):
    """Handle errors during scraping process"""
    
    @abc.abstractmethod
    def handle_page_error(self, page_num: int, error: Exception) -> None:
        pass
    
    @abc.abstractmethod
    def handle_critical_error(self, error: Exception) -> None:
        pass
    
    @abc.abstractmethod
    def get_errors(self) -> List[str]:
        pass
