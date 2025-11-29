"""Factory for FileLinkProcessor implementations"""
from src.core.config import config
from src.infrastructure.processors.html.file_link_processor import FileLinkProcessor
from src.infrastructure.processors.html.file_link_processor_refactored import FileLinkProcessorRefactored

def create_file_link_processor():
    """Create appropriate FileLinkProcessor based on feature flags"""
    if config.feature_flags.use_refactored_file_link_processor:
        return FileLinkProcessorRefactored()
    else:
        return FileLinkProcessor()
