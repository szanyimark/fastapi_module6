import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode
import httpx

from .providers import PROVIDERS, OAuthProvider


def _get_provider_config(provider: str | OAuthProvider) -> dict:
    """Get provider configuration by name or enum."""
    if isinstance(provider, OAuthProvider):
        provider = provider.value
    
    cfg = PROVIDERS.get(provider)
    if not cfg:
        raise ValueError(f"Unsupported provider: {provider}")
    
    client_id = os.getenv(cfg["client_id_env"]) or ""
    client_secret = os.getenv(cfg["client_secret_env"]) or ""
    if not client_id or not client_secret:
        raise RuntimeError(f"Missing credentials for provider '{provider}' - set {cfg['client_id_env']} and {cfg['client_secret_env']}")
    
    # Return merged copy with resolved credentials
    merged = dict(cfg)
    merged["client_id"] = client_id
    merged["client_secret"] = client_secret
    return merged


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def get_oauth_authorization_url(provider: str | OAuthProvider, redirect_uri: str, scope: str | None = None) -> tuple[str, str, str]:
    """Generate OAuth authorization URL with state and PKCE for a provider."""
    cfg = _get_provider_config(provider)
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": scope or cfg["default_scope"],
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    # Provider-specific auth params
    params.update(cfg.get("extra_auth_params", {}))

    url = f"{cfg['authorize_url']}?{urlencode(params)}"
    return url, state, code_verifier


async def exchange_oauth_code_for_token(provider: str | OAuthProvider, code: str, redirect_uri: str, code_verifier: str) -> dict:
    """Exchange authorization code for access token with PKCE for a provider."""
    cfg = _get_provider_config(provider)
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    data.update(cfg.get("token_body_extra", {}))

    async with httpx.AsyncClient() as client:
        response = await client.post(
            cfg["token_url"],
            data=data,
            headers=cfg.get("token_headers", {}),
        )
        return response.json()


async def get_oauth_user_info(provider: str | OAuthProvider, access_token: str) -> dict:
    """Fetch user info from provider API."""
    cfg = _get_provider_config(provider)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            cfg["user_info_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


async def get_oauth_user_emails(provider: str | OAuthProvider, access_token: str) -> list[dict]:
    """Fetch user emails if provider exposes a dedicated endpoint (GitHub)."""
    cfg = _get_provider_config(provider)
    emails_url = cfg.get("emails_url")
    if not emails_url:
        return []
    async with httpx.AsyncClient() as client:
        response = await client.get(
            emails_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()
