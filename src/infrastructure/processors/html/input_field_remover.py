from typing import Dict, Any
from bs4 import BeautifulSoup
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor

class InputFieldRemover(IRawBlockProcessor):
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body_html = raw_data.get("body_html", "") or ""
        soup = BeautifulSoup(body_html, "html.parser")
        # Remove answer input fields or hidden tokens that confuse downstream extraction
        for inp in soup.find_all("input"):
            name = inp.get("name", "").lower()
            if "answer" in name or inp.get("type") in ("hidden", "submit"):
                inp.decompose()
        raw_data["body_html"] = str(soup)
        return raw_data
