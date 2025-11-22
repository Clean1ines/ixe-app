from typing import Dict, Any
from bs4 import BeautifulSoup
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor

class UnwantedElementRemover(IRawBlockProcessor):
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body = raw_data.get("body_html", "") or ""
        soup = BeautifulSoup(body, "html.parser")
        # Heuristics: remove scripts, style, ads, share buttons, input[type=button], forms
        for selector in ["script", "style", ".advert", ".ads", ".share", "button", "form", ".cookie-banner"]:
            for el in soup.select(selector):
                el.decompose()
        raw_data["body_html"] = str(soup)
        return raw_data
