from typing import Optional, Tuple, List, Any, Dict
from bs4 import Tag
import re
import logging
from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class ElementIdentifier:
    """
    Service for identifying core elements (qblock, header) from HTML block groups.
    
    Business Rules:
    - Contains pure logic for element identification
    - No side effects, only data transformation
    - Fallback strategies are explicit and testable
    """
    
    @staticmethod
    def identify_core_elements(
        block_elements: List[Tag], 
        block_index: int
    ) -> Tuple[Optional[Tag], Optional[Tag]]:
        """
        Identify header and qblock elements from a group of HTML elements.
        
        Args:
            block_elements: List of HTML elements belonging to one task
            block_index: Position of block on page (for logging)
            
        Returns:
            Tuple of (header_container, qblock) or (None, None) if identification fails
        """
        qblock = ElementIdentifier._find_qblock(block_elements)
        header_container = ElementIdentifier._find_header_container(block_elements, qblock)
        
        if not qblock or not header_container:
            logger.warning(f"Block {block_index} missing required elements (qblock: {qblock is not None}, header: {header_container is not None})")
            return None, None
            
        return header_container, qblock
    
    @staticmethod
    def _find_qblock(elements: List[Tag]) -> Optional[Tag]:
        """Pure function to identify qblock element."""
        # Primary strategy: look for element with class 'qblock'
        for element in elements:
            if 'qblock' in element.get('class', []):
                return element
        
        # Fallback: element with most text content
        elements_with_text = [(elem, len(elem.get_text(strip=True))) for elem in elements]
        if not elements_with_text:
            return None
            
        elements_with_text.sort(key=lambda x: x[1], reverse=True)
        return elements_with_text[0][0] if elements_with_text[0][1] > 50 else None
    
    @staticmethod
    def _find_header_container(elements: List[Tag], qblock: Optional[Tag]) -> Optional[Tag]:
        """Pure function to identify header container."""
        # Primary strategy: look for elements with header-related identifiers
        for element in elements:
            element_id = element.get('id', '')
            element_classes = element.get('class', [])
            
            if element_id.startswith('i'):
                return element
                
            if any(cls.lower() in ['header', 'info', 'task-header', 'task-info'] for cls in element_classes):
                return element
        
        # Secondary strategy: look for elements with header-related text
        for element in elements:
            text = element.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['задание', 'task', 'кэс', 'кос', 'кодификатор']):
                return element
        
        # Fallback: first element that's not the qblock
        if qblock is not None:
            for element in elements:
                if element != qblock:
                    return element
        
        return elements[0] if elements else None
