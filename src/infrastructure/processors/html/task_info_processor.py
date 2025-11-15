"""
Infrastructure adapter implementing domain interface for processing task info buttons in HTML blocks.

This module provides the `TaskInfoProcessor` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for processing task info button
onclick attributes within a single problem block pair (header_container, qblock).
"""
import logging
import re
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, Any
# from domain.interfaces.html_processor import IHTMLProcessor # УДАЛЯЕМ СТАРЫЙ ИМПОРТ
from src.domain.interfaces.html_processing.i_html_processor import IHTMLProcessor # Импортируем правильный интерфейс

logger = logging.getLogger(__name__)

class TaskInfoProcessor(IHTMLProcessor):
    """
    Infrastructure adapter implementing IHTMLProcessor for task info button processing.
    
    Business Rules:
    - Updates onclick attributes for task info buttons
    - Replaces dynamic task ID with the block index
    - Logs changes made to onclick attributes
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
        Process a single HTML block pair and update task info button onclick attributes.

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
        logger.debug(f"Processing task info buttons for block {block_index} in subject {subject_info.alias}.")

        # Convert the qblock content to string for processing
        qblock_content = str(qblock)

        # Update onclick attributes for task info buttons
        # Look for onclick attributes that contain ShowTaskInfo calls
        # This regex finds onclick="javascript:ShowTaskInfo(...)" and replaces the argument with the block_index
        pattern = r"onclick=[\"']javascript:ShowTaskInfo\([^)]+\)[\"']"
        updated_content = re.sub(pattern,
                                f'onclick="javascript:ShowTaskInfo(\'{block_index}\')"',
                                qblock_content)

        # Parse back to BeautifulSoup object
        updated_qblock_soup = BeautifulSoup(updated_content, 'html.parser')
        updated_qblock = updated_qblock_soup.find('div', class_='qblock') or updated_qblock_soup.find('div')
        if not updated_qblock:
            # If no qblock found, return the first div
            updated_qblock = updated_qblock_soup.find('div')

        # Return the processed block data
        return {
            'header_container': header_container, # Header might not change in this processor
            'qblock': updated_qblock, # Return the *newly created* soup object with changes
            'block_index': block_index,
            'subject': subject_info.subject_name, # Use subject name from VO
            'base_url': base_url
        }

