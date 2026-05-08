from aiohttp import ClientSession

class HttpClient:
    def __init__(self):
        self.session: ClientSession | None = None

    def init(self):
        self.session = ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

http_client = HttpClient()
