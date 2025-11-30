from .fake_browser_page import FakeBrowserPage

class FakeBrowserService:
    """
    Fake Browser Service that provides a FakeBrowserPage.
    Mocking the IBrowserService interface.
    """
    def __init__(self):
        self.page = FakeBrowserPage()
        self._closed = False

    async def launch(self):
        pass

    async def get_page(self) -> FakeBrowserPage:
        return self.page

    async def close(self):
        self._closed = True
