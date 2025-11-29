"""
Application service for processing HTML blocks using IRawBlockProcessor architecture.

This service coordinates:
1. Extraction of raw data from HTML blocks using MetadataExtractorAdapter
2. Processing raw data through a chain of IRawBlockProcessor
3. Creating Problem entities from processed raw data
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor
from src.domain.models.problem import Problem
from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.infrastructure.adapters.html_processing.metadata_extractor_adapter import MetadataExtractorAdapter

logger = logging.getLogger(__name__)

class HTMLBlockProcessingService:
    """
    Application service for processing HTML blocks in the new IRawBlockProcessor architecture.
    """

    def __init__(
        self,
        metadata_extractor: MetadataExtractorAdapter,
        raw_processors: Optional[List[IRawBlockProcessor]] = None,
    ):
        """
        Initialize with metadata extractor and raw data processors.
        
        Args:
            metadata_extractor: Adapter for extracting raw data from HTML blocks
            raw_processors: List of processors that work on raw data dicts
        """
        self.metadata_extractor = metadata_extractor
        self.raw_processors = raw_processors or []

    async def process_block(
        self,
        block_elements: list,
        block_index: int,
        context: Dict[str, Any],
    ) -> Optional[Problem]:
        """
        Process a block of HTML elements into a Problem entity using new architecture.

        Args:
            block_elements: List of HTML elements belonging to one task
            block_index: Index of the block in the page
            context: Processing context containing subject_info, source_url, etc.

        Returns:
            Problem entity or None if processing fails
        """
        try:
            # Import here to avoid circular imports
            from src.application.services.html_parsing.element_identifier import ElementIdentifier
            
            # 1. Identify core elements from block_elements
            header_container, qblock = ElementIdentifier.identify_core_elements(
                block_elements, block_index
            )
            
            if not header_container or not qblock:
                logger.warning(f"Could not identify core elements for block {block_index}")
                return None

            logger.debug(f"Processing block {block_index} for subject {context['subject_info'].official_name}")

            # 2. Extract raw data using metadata extractor
            raw_data = self.metadata_extractor.extract(
                processed_header=header_container,
                processed_qblock=qblock,
                block_index=block_index,
                subject_info=context['subject_info'],
                source_url=context.get('source_url', ''),
                run_folder_page=context.get('run_folder_page', Path('.'))
            )

            # 3. Apply raw data processors
            processed_data = await self._apply_raw_processors(raw_data, context)

            # 4. Create Problem entity
            problem = self._create_problem_from_raw_data(processed_data)
            return problem

        except Exception as e:
            logger.error(f"Error processing block {block_index}: {e}", exc_info=True)
            return None

    async def _apply_raw_processors(
        self, 
        raw_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply chain of IRawBlockProcessor to raw data.
        
        Args:
            raw_data: Initial raw data from metadata extractor
            context: Processing context
            
        Returns:
            Processed raw data
        """
        processed_data = raw_data
        
        for processor in self.raw_processors:
            try:
                logger.debug(f"Applying raw processor {processor.__class__.__name__}")
                processed_data = await processor.process(processed_data, context)
            except Exception as e:
                logger.error(f"Error applying processor {processor.__class__.__name__}: {e}")
                # Continue with next processor
                continue
                
        return processed_data

    def _create_problem_from_raw_data(self, raw_data: Dict[str, Any]) -> Problem:
        """
        Create Problem entity from raw data.
        """
        return Problem(
            problem_id=raw_data['problem_id'],
            subject_name=raw_data['subject_name'],
            text=raw_data['text'],
            source_url=raw_data['source_url'],
            answer=raw_data.get('answer'),
            images=raw_data.get('images', []),
            files=raw_data.get('files', []),
            kes_codes=raw_data.get('kes_codes', []),
            topics=raw_data.get('topics', []),
            kos_codes=raw_data.get('kos_codes', []),
            difficulty_level=raw_data.get('difficulty_level'),
            task_number=raw_data.get('task_number'),
            exam_part=raw_data.get('exam_part'),
            fipi_proj_id=raw_data.get('fipi_proj_id'),
            created_at=raw_data.get('created_at'),
            updated_at=raw_data.get('updated_at')
        )
