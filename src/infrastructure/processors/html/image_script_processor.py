import asyncio
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
from src.domain.interfaces.html_processing.i_raw_block_processor import IRawBlockProcessor

class ImageScriptProcessor(IRawBlockProcessor):
    async def process(self, raw_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        body_html = raw_data.get("body_html", "") or ""
        base_url = context.get("base_url", "")
        run_folder: Path = Path(context.get("run_folder_page", Path(".")))
        files_prefix = context.get("files_location_prefix", "")
        # NEW: Get playwright_page directly from context
        playwright_page = context.get("playwright_page", None)
        # We no longer rely on 'downloader' from context

        if not playwright_page:
            # If no page is available, we cannot download images in the correct session
            # Log a warning and return early, or handle as needed
            print("WARNING: No playwright page available in context for image download. Skipping image processing.")
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
            # src = docs/E040A72A1A3DABA14C90C97E0B6EE7DC/...
            # base_url для разрешения = https://ege.fipi.ru/bank/...
            # qfiles_location="../../" означает подняться на 2 уровня от текущей страницы (bank/)
            # ../../ из /bank/ -> https://ege.fipi.ru/
            # full_url = https://ege.fipi.ru/ + src
            # Это даст правильный путь: https://ege.fipi.ru/docs/...
            
            # Мы знаем, что страница загружена с https://ege.fipi.ru/bank/...
            # qfiles_location="../../" -> поднимается на 2 уровня: /bank/ -> (корень домена)
            # Поэтому базовый URL для разрешения src - это корень домена ege.fipi.ru
            base_for_resolution = "https://ege.fipi.ru/"
            full_url = urljoin(base_for_resolution, src.lstrip('/'))
            
            print(f"DEBUG: Attempting to download image from URL (via page): {full_url}")
            
            # Получаем имя файла и очищаем его от недопустимых символов
            filename = Path(urlparse(full_url).path).name
            if not filename:
                filename = f"img_{idx}.png"
            
            # Очищаем имя файла от недопустимых символов для пути
            # Заменяем недопустимые символы (включая пробелы и скобки) на подчеркивания или удаляем их
            # Это предотвратит ошибку [Errno 21] Is a directory
            clean_filename = re.sub(r'[<>:"/\\|?*()]+', '_', filename)
            # Убираем двойные подчеркивания и подчеркивания на концах
            clean_filename = re.sub(r'_+', '_', clean_filename).strip('_')
            # Если имя файла начинается с точки (например, .png), добавляем префикс
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
            
            # NEW: Use playwright_page.request.get, this is the core change
            try:
                # Use the same session/cookies as the page
                # NEW: Add ignore_https_errors=True to handle certificate issues
                response = await playwright_page.request.get(full_url, ignore_https_errors=True)
                if response.ok:
                    content = await response.body() # Get the binary content
                    # NEW: Check if dest_path is a directory before writing
                    if dest_path.is_dir():
                        # If it's a directory, remove it to make place for the file
                        # This is the fix for the "Is a directory" error
                        print(f"INFO: Removing directory {dest_path} to save file with the same name.")
                        import shutil
                        shutil.rmtree(dest_path)
                    # NEW: Add explicit check for parent directory creation
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    # Write the content to the destination file
                    with open(dest_path, 'wb') as f:
                        f.write(content)
                    # Update the img tag src to point to the local file
                    rel = dest_path.relative_to(run_folder)
                    local_ref = str(rel).replace("\\", "/")
                    img_tag['src'] = f"{files_prefix}{local_ref}"
                    images_local.append(local_ref)
                    downloaded_files.add(clean_filename)
                    print(f"✅ Downloaded (via page): {clean_filename}")
                    print(f"   Saved to: {dest_path}") # NEW: Print the actual save location
                else:
                    print(f"❌ Failed to download via page (status {response.status}): {clean_filename}")
            except Exception as e:
                print(f"❌ Error downloading via page {clean_filename}: {e}")

        # Запускаем загрузку последовательно чтобы избежать дублирования
        for i, img_tag in enumerate(img_tags):
            await download_image(img_tag, i)

        raw_data["body_html"] = str(soup)
        raw_data["images"] = images_local
        return raw_data
