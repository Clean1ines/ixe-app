from abc import ABC, abstractmethod
from typing import Dict, Any


class IHTMLProcessor(ABC):
    """Interface for HTML processing components."""

    @abstractmethod
    def process_html_block(self, html_block: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process an HTML block and extract structured data.
        
        Args:
            html_block: The HTML content to process
            context: Additional context for processing
            
        Returns:
            Dict[str, Any]: Processed data
        """
        pass
