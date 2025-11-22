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
        downloader = context.get("downloader") or context.get("asset_downloader")

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
            if src.startswith(('http://', 'https://')):
                full_url = src
            else:
                # Для относительных путей просто добавляем к базовому URL банка
                full_url = urljoin("https://ege.fipi.ru/bank/", src)
            
            # Получаем имя файла
            filename = Path(urlparse(full_url).path).name
            if not filename:
                filename = f"img_{idx}.png"
            
            # Пропускаем если уже скачали
            if filename in downloaded_files:
                return
                
            # Скачиваем
            dest_dir = run_folder / "assets"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename
            
            try:
                success = await downloader.download(full_url, dest_path)
                if success:
                    rel = dest_path.relative_to(run_folder)
                    local_ref = str(rel).replace("\\", "/")
                    img_tag['src'] = f"{files_prefix}{local_ref}"
                    images_local.append(local_ref)
                    downloaded_files.add(filename)
                    print(f"✅ Downloaded: {filename}")
            except Exception as e:
                print(f"❌ Error: {filename} - {e}")

        # Запускаем загрузку последовательно чтобы избежать дублирования
        for i, img_tag in enumerate(img_tags):
            await download_image(img_tag, i)

        raw_data["body_html"] = str(soup)
        raw_data["images"] = images_local
        return raw_data
