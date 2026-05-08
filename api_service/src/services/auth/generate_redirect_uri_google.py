import urllib.parse
import secrets

from src.config import OAUTH2_GOOGLE_CLIENT_ID

class GenerateOauthRedirectUri:
    @staticmethod
    def generate_google_oauth_redirect_uri():
        # random_state = secrets.token_urlsafe(16)
        
        query_params = {
            "client_id": OAUTH2_GOOGLE_CLIENT_ID,
            "redirect_uri": "http://localhost:8000/users/oauth2-google/callback",
            "response_type": "code",
            "scope": " ".join([
                "openid",
                "profile",
                "email",
            ]),
            # "state": random_state,
        }

        query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        return f"{base_url}?{query_string}"