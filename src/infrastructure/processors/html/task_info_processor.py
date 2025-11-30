from typing import Any, Dict
import re
from bs4 import BeautifulSoup
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor


class TaskInfoProcessor(IRawBlockProcessor):
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Extract textual fields from header_html
        header_html = raw_data.get("header_html", "") or ""
        soup = BeautifulSoup(header_html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        # Task number
        task_match = re.search(r"(?:Задание|Task)\s+(\d+)", text, re.IGNORECASE)
        if task_match:
            raw_data["task_number"] = int(task_match.group(1))
        # KES codes (simple heuristic)
        kes_matches = re.findall(r'(?:КЭС|кодификатор)[:\s]*([0-9.,\s-]+)', text, re.IGNORECASE)
        kes_codes = []
        for m in kes_matches:
            for part in re.split(r'[,\s]+', m.strip()):
                if part:
                    kes_codes.append(part.strip().strip(","))
        raw_data["kes_codes"] = kes_codes
        # KOS codes
        kos_matches = re.findall(r'(?:КОС|требование)[:\s]*([0-9.,\s-]+)', text, re.IGNORECASE)
        kos_codes = []
        for m in kos_matches:
            for part in re.split(r'[,\s]+', m.strip()):
                if part:
                    kos_codes.append(part.strip().strip(","))
        raw_data["kos_codes"] = kos_codes
        # Title fallback
        raw_data.setdefault("title", text[:200] if text else None)
        return raw_data
