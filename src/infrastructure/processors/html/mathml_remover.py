"""
Infrastructure adapter implementing domain interface for removing MathML elements from HTML blocks.

This module provides the `MathMLRemover` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for removing MathML elements
(math, mml:math) within a single problem block pair (header_container, qblock).
"""
import logging
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, Any
# from domain.interfaces.html_processor import IHTMLProcessor # УДАЛЯЕМ СТАРЫЙ ИМПОРТ
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем правильный интерфейс

logger = logging.getLogger(__name__)

class MathMLRemover(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for removing MathML elements.
    
    Business Rules:
    - Removes 'math' and 'mml:math' tags
    - Logs the number of removed MathML elements
    - Returns processed block data
    """

    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str, # Use subject name string
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and remove MathML elements.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics"). This is a string.
            base_url: The base URL of the scraped page (e.g., https://ege.fipi.ru/bank/{proj_id}).
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing the updated block data.
            Example: {
                "header_container": updated_header_container,
                "qblock": updated_qblock,
                "block_index": int,
                "subject": str, # subject_info.subject_name
                "base_url": str,
            }
        """
        logger.debug(f"Removing MathML elements for block {block_index} in subject {subject}.")

        # Process the qblock content to remove MathML
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')

        # Remove math and mml:math tags
        removed_count = 0
        for tag in soup.find_all(['math', 'mml:math']):
            tag.decompose()
            removed_count += 1

        logger.debug(f"Removed {removed_count} MathML elements from block {block_index}.")

        # Update the qblock with processed content
        processed_qblock = soup.find('div', class_='qblock') or soup.find('div')

        # Return the processed block data
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': processed_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject, # Use the string subject
            'base_url': base_url
        }
