import asyncio
from typing import Dict, Any
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor

class FileLinkProcessor(IRawBlockProcessor):
    """
    Downloads file links (pdf/doc/zip) and collects local paths.
    Expects 'downloader', 'run_folder_page', 'files_location_prefix', 'base_url' in context.
    """
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body_html = raw_data.get("body_html", "") or ""
        base_url = context.get("base_url", "")
        run_folder: Path = Path(context.get("run_folder_page", Path(".")))
        files_prefix = context.get("files_location_prefix", "")
        downloader = context.get("downloader") or context.get("asset_downloader")

        soup = BeautifulSoup(body_html, "html.parser")
        file_links_local = raw_data.get("files", [])

        # selectors: a[href$=".pdf"], a.file-link
        link_tags = soup.find_all("a", href=True)
        # Filter for file-like links
        candidates = [a for a in link_tags if any(a['href'].lower().endswith(ext) for ext in ('.pdf', '.doc', '.docx', '.zip', '.rar')) or 'file' in (a.get('class') or [])]

        semaphore = asyncio.Semaphore(6)
        async def fetch_and_record(a_tag, idx):
            href = a_tag.get('href')
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            filename = Path(parsed.path).name or f"file_{idx}.dat"
            dest_dir = run_folder / "assets"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename
            try:
                async with semaphore:
                    ok = await downloader.download(full_url, dest_path)
                if ok:
                    rel = dest_path.relative_to(run_folder)
                    local_ref = str(rel).replace("\\", "/")
                    # optionally update href
                    a_tag['href'] = f"{files_prefix}{local_ref}"
                    file_links_local.append(local_ref)
            except Exception:
                return

        tasks = [fetch_and_record(tag, i) for i, tag in enumerate(candidates)]
        if tasks:
            await asyncio.gather(*tasks)

        raw_data["body_html"] = str(soup)
        raw_data["files"] = file_links_local
        return raw_data
