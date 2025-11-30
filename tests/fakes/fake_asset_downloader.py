from typing import Optional, Dict, Any
from pathlib import Path
from src.domain.interfaces.external_services.i_asset_downloader import IAssetDownloader # Если этот интерфейс существует

class FakeAssetDownloader:
    """
    Фейковый загрузчик активов (Fake), который имитирует успешную загрузку
    и возвращает фиксированный путь для проверки логики FileLinkProcessor.
    Заменяет AsyncMock для более надежного тестирования.
    """
    
    def __init__(self):
        # Хранит информацию о вызовах, чтобы заменить assert_called_once
        self.download_calls = 0
        self.download_bytes_calls = 0

    async def download(self, url: str, directory: Path, filename: Optional[str] = None) -> Path:
        """Имитирует асинхронную загрузку файла."""
        self.download_calls += 1
        # Имитация возврата локального пути к файлу
        if filename:
            return directory / filename
        return directory / Path(url).name

    async def download_bytes(self, url: str) -> bytes:
        """Имитирует асинхронную загрузку данных."""
        self.download_bytes_calls += 1
        return b"fake_content"

    # Методы для проверки в тесте
    def assert_download_called_n_times(self, n: int):
        assert self.download_calls == n, f"Ожидалось {n} вызовов download, получено {self.download_calls}"
