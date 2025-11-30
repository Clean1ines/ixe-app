from typing import Any, Dict
import abc


class IRawBlockProcessor(abc.ABC):
    """
    Domain-level processor interface for processing a raw block dict.

    The contract: accept a raw_data dict and a context dict and return a
    (possibly modified) raw_data dict. This keeps processors testable and small.
    """
    @abc.abstractmethod
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the raw_data and return the resulting raw_data (may be same object mutated).
        """
        raise NotImplementedError
