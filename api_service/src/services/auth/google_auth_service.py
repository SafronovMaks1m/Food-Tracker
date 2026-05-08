from src.config import OAUTH2_GOOGLE_CLIENT_ID, OAUTH2_GOOGLE_TOKEN_URL, OAUTH2_GOOGLE_CLIENT_SECRET
from src.services.aiohttp_sessions.create_pull_sessions import http_client
class GoogleAuthService:
    @classmethod
    async def get_responce_google(cls, code):
        async with http_client.session.post(
            url=OAUTH2_GOOGLE_TOKEN_URL,
            data={
                "client_id": OAUTH2_GOOGLE_CLIENT_ID,
                "client_secret": OAUTH2_GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:8000/users/oauth2-google/callback",
                "code": code,
            }
        ) as response:
            result = {
                "status": response.status,
                "Content-Type": response.headers.get("Content-Type", "")
            }
            if response.status == 200:
                body = await response.json()
                result.update({"body": body})
            return result
                