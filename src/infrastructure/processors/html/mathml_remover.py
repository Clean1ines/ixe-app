from typing import Any, Dict
from bs4 import BeautifulSoup
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor


class MathMLRemover(IRawBlockProcessor):
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body = raw_data.get("body_html", "") or ""
        soup = BeautifulSoup(body, "html.parser")
        # remove <math> and <mi>/<mo> etc if present
        for m in soup.find_all("math"):
            m.decompose()
        raw_data["body_html"] = str(soup)
        return raw_data
