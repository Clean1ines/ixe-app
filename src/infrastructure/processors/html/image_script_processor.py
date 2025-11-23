import asyncio
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader

class ImageScriptProcessor(IRawBlockProcessor):
    def __init__(self, asset_downloader: IAssetDownloader):
        """
        Initialize with an asset downloader implementation.

        Args:
            asset_downloader: Implementation of IAssetDownloader to use for image downloads.
        """
        self._asset_downloader = asset_downloader

    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body_html = raw_data.get("body_html", "") or ""
        base_url = context.get("base_url", "")
        run_folder: Path = Path(context.get("run_folder_page", Path(".")))
        files_prefix = context.get("files_location_prefix", "")

        # Get asset_downloader from context as fallback if not injected via constructor
        asset_downloader = context.get("asset_downloader", self._asset_downloader)

        if not asset_downloader:
            print("ERROR: No asset_downloader available in context or constructor for ImageScriptProcessor. Cannot download images.")
            raw_data["body_html"] = body_html
            raw_data["images"] = []
            return raw_data

        soup = BeautifulSoup(body_html, "html.parser")
        images_local = raw_data.get("images", [])

        # Обрабатываем скрипты ShowPictureQ - создаем теги img
        scripts = soup.find_all('script', string=re.compile(r'ShowPictureQ'))
        for script in scripts:
            matches = re.findall(r"ShowPictureQ\('([^']+)'\)", script.string)
            for match in matches:
                relative_path = match
                # Создаем тег img для каждого изображения из скрипта
                img_tag = soup.new_tag('img')
                img_tag['src'] = relative_path
                img_tag['class'] = 'dynamic-image'
                script.insert_after(img_tag)

        # Скачиваем ВСЕ изображения (включая созданные из скриптов)
        img_tags = soup.find_all("img")
        downloaded_files = set()

        async def download_image(img_tag, idx):
            src = img_tag.get("src")
            if not src:
                return

            # Формируем URL - используем ТОЛЬКО относительные пути как есть
            # Используем qfiles_location="../../" логику из JS
            base_for_resolution = "https://ege.fipi.ru/"
            full_url = urljoin(base_for_resolution, src.lstrip('/'))

            print(f"DEBUG: Attempting to download image from URL (via asset_downloader): {full_url}")

            # Получаем имя файла и очищаем его от недопустимых символов
            filename = Path(urlparse(full_url).path).name
            if not filename:
                filename = f"img_{idx}.png"

            # Очищаем имя файла от недопустимых символов для пути
            clean_filename = re.sub(r'[<>:"/\\|?*()]+', '_', filename)
            clean_filename = re.sub(r'_+', '_', clean_filename).strip('_')
            if clean_filename.startswith('.'):
                clean_filename = f"image_{idx}{clean_filename}"

            print(f"DEBUG: Using cleaned filename: {clean_filename}")

            # Пропускаем если уже скачали
            if clean_filename in downloaded_files:
                return

            # Скачиваем
            dest_dir = run_folder / "assets"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / clean_filename

            try:
                # Use the asset_downloader to get the content
                content_bytes = await asset_downloader.download_bytes(full_url)
                if content_bytes is not None:
                    # NEW: Check if dest_path is a directory before writing
                    if dest_path.is_dir():
                        print(f"INFO: Removing directory {dest_path} to save file with the same name.")
                        import shutil
                        shutil.rmtree(dest_path)
                    # NEW: Add explicit check for parent directory creation
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    # Write the content to the destination file
                    with open(dest_path, 'wb') as f:
                        f.write(content_bytes)
                    # Update the img tag src to point to the local file
                    rel = dest_path.relative_to(run_folder)
                    local_ref = str(rel).replace("\\", "/")
                    img_tag['src'] = f"{files_prefix}{local_ref}"
                    images_local.append(local_ref)
                    downloaded_files.add(clean_filename)
                    print(f"✅ Downloaded (via asset_downloader): {clean_filename}")
                    print(f"   Saved to: {dest_path}")
                else:
                    print(f"❌ Failed to download via asset_downloader: {clean_filename}")
            except Exception as e:
                print(f"❌ Error downloading via asset_downloader {clean_filename}: {e}")

        # Запускаем загрузку последовательно чтобы избежать дублирования
        for i, img_tag in enumerate(img_tags):
            await download_image(img_tag, i)

        raw_data["body_html"] = str(soup)
        raw_data["images"] = images_local
        return raw_data
