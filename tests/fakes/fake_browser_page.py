from typing import Dict, Any, List

class FakeBrowserPage:
    """
    Fake-реализация объекта браузерной страницы.
    Используется для тестирования компонентов, работающих с BrowserPage.
    """
    
    def __init__(self, url: str = "about:blank"):
        # Карта URL -> HTML-контент
        self._content_map: Dict[str, str] = {}
        self._url: str = url
        self._goto_calls: List[Dict[str, Any]] = []

    async def set_current_url(self, url: str):
        """Метод для настройки текущего URL страницы для тестов."""
        self._url = url

    async def goto(self, url: str, wait_until: str = "load", timeout: int = 30000):
        """
        Имитирует переход по URL. 
        Добавлен 'wait_until' для совместимости с кодом IframeHandler.
        """
        self._goto_calls.append({"url": url, "timeout": timeout, "wait_until": wait_until})
        self._url = url
        
        # Если контента для этого URL нет, имитируем ошибку (для тестов, где это нужно)
        if url not in self._content_map:
            raise Exception(f"Navigation error: Content not mapped for {url}")

    async def content(self) -> str:
        """Возвращает контент из карты по текущему URL."""
        return self._content_map.get(self._url, "")

    def set_content_for_url(self, url: str, content: str):
        """Настраивает контент, который будет возвращен для конкретного URL."""
        self._content_map[url] = content

    def get_goto_calls(self) -> List[Dict[str, Any]]:
        """Возвращает список всех вызовов goto (для проверки взаимодействия)."""
        return self._goto_calls

    @property
    def url(self) -> str:
        """Возвращает текущий URL."""
        return self._url
