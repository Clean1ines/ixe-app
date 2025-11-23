import asyncio
from pathlib import Path
from src.dependency_injection.composition_root import create_scraping_components

async def create_tables_and_get_components():
    base_run_folder = Path("test_data")
    (scrape_use_case, browser_service, 
     asset_downloader_impl) = create_scraping_components(base_run_folder)
    return asset_downloader_impl

async def debug_download():
    # Получаем компоненты
    asset_downloader_impl = await create_tables_and_get_components()
    
    # Создаем адаптер для загрузки
    from src.infrastructure.adapters.external_services.asset_downloader_adapter import AssetDownloaderAdapter
    adapter = AssetDownloaderAdapter(asset_downloader_impl, Path("test_data/page_1/assets"))
    
    # Пробуем загрузить один файл напрямую
    test_url = "https://ege.fipi.ru/bank/docs/E040A72A1A3DABA14C90C97E0B6EE7DC/questions/002DB930E40A887944ED4C0F49E9DF34/xs3qstsrc002DB930E40A887944ED4C0F49E9DF34_1_1480426041.png"
    result = await adapter.download(test_url, Path("test_data/page_1/assets/test.png"))
    
    print(f"Direct download result: {result}")
    print(f"File exists: {result.exists() if result else False}")

asyncio.run(debug_download())
