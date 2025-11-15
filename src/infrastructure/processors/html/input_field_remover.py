"""
Infrastructure adapter implementing domain interface for removing input fields from HTML blocks.

This module provides the `InputFieldRemover` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for removing input fields
with name 'answer' within a single problem block pair (header_container, qblock).
"""
import logging
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, Any
# from domain.interfaces.html_processor import IHTMLProcessor # УДАЛЯЕМ СТАРЫЙ ИМПОРТ
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем правильный интерфейс

logger = logging.getLogger(__name__)

class InputFieldRemover(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for removing input fields.
    
    Business Rules:
    - Removes input fields with name 'answer'
    - Logs the number of removed input fields
    - Returns processed block data
    """

    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject_info: 'SubjectInfo', # Используем строковую аннотацию
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and remove input fields with name 'answer'.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject_info: The SubjectInfo object containing subject details.
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
        logger.debug(f"Removing input fields for block {block_index} in subject {subject_info.alias}.")

        # Process the qblock content to remove input fields
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')

        # Remove input fields with name 'answer'
        removed_count = 0
        for inp in soup.find_all('input', attrs={'name': 'answer'}):
            inp.decompose()
            removed_count += 1

        logger.debug(f"Removed {removed_count} input fields with name 'answer' from block {block_index}.")

        # Update the qblock with processed content
        processed_qblock = soup.find('div', class_='qblock') or soup.find('div')

        # Return the processed block data
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': processed_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject_info.subject_name, # Use subject name from VO
            'base_url': base_url
        }

