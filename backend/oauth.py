import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode
import httpx

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise RuntimeError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables are required")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE_URL = "https://api.github.com"


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def get_authorization_url(redirect_uri: str, scope: str = "user:email") -> tuple[str, str, str]:
    """Generate GitHub OAuth authorization URL with state and PKCE."""
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "allow_signup": "true"
    }
    url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return url, state, code_verifier


async def exchange_code_for_token(code: str, redirect_uri: str, code_verifier: str) -> dict:
    """Exchange authorization code for access token with PKCE."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_ACCESS_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
        )
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """Fetch user info from GitHub API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


async def get_user_emails(access_token: str) -> list[dict]:
    """Fetch user emails from GitHub API (requires user:email scope)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()
