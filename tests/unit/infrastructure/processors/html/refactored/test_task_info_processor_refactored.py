"""Tests for TaskInfoProcessor refactoring"""
import pytest
from src.infrastructure.processors.html.task_info_processor import TaskInfoProcessor

class TestTaskInfoProcessorRefactored:
    """Test suite for refactored TaskInfoProcessor"""
    
    @pytest.fixture
    def processor(self):
        return TaskInfoProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_task_number(self, processor):
        """Test extracting task number from header"""
        raw_data = {
            "header_html": '<div>Задание 15</div>',
            "kes_codes": [],
            "kos_codes": []
        }
        
        result = await processor.process(raw_data, {})
        
        assert result["task_number"] == 15
    
    @pytest.mark.asyncio
    async def test_extract_kes_codes(self, processor):
        """Test extracting KES codes"""
        raw_data = {
            "header_html": '<div>КЭС: 1.2, 3.4</div>',
            "kes_codes": [],
            "kos_codes": []
        }
        
        result = await processor.process(raw_data, {})
        
        assert "1.2" in result["kes_codes"]
        assert "3.4" in result["kes_codes"]
