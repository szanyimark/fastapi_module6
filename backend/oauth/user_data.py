"""OAuth user data extraction utilities for different providers."""

from typing import Tuple

from fastapi import HTTPException
from . import get_oauth_user_emails
from .providers import OAuthProvider


async def extract_github_user_data(user_info: dict, access_token: str) -> Tuple[str, str, str]:
    """Extract GitHub-specific user data (username, email, fullname)."""
    username = user_info.get("login")
    if not username:
        raise HTTPException(status_code=400, detail="Failed to retrieve user information")
    
    fullname = user_info.get("name")
    email = user_info.get("email")
    
    # GitHub email fallback
    if not email:
        emails = await get_oauth_user_emails(OAuthProvider.GITHUB, access_token)
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        email = (primary or (emails[0] if emails else None) or {}).get("email")
        if not email:
            email = f"{username}@users.noreply.github.com"
    
    return username, email, fullname


def extract_google_user_data(user_info: dict) -> Tuple[str, str, str]:
    """Extract Google-specific user data (username, email, fullname)."""
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Failed to retrieve user information")
    
    fullname = user_info.get("name", email.split("@")[0])
    username = email.split("@")[0].replace(".", "_")
    
    return username, email, fullname


async def extract_provider_user_data(
    provider: OAuthProvider, 
    user_info: dict, 
    access_token: str
) -> Tuple[str, str, str]:
    """Extract user data based on OAuth provider."""
    if provider == OAuthProvider.GITHUB:
        return await extract_github_user_data(user_info, access_token)
    elif provider == OAuthProvider.GOOGLE:
        return extract_google_user_data(user_info)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")