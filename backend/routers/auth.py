import os
from fastapi import APIRouter, HTTPException, Cookie, Response, Depends
from fastapi.responses import RedirectResponse
from oauth import (
    get_oauth_authorization_url,
    exchange_oauth_code_for_token,
    get_oauth_user_info,
)
from oauth.providers import OAuthProvider
from utils import create_access_token
from sqlalchemy.orm import Session
from database.database import get_db
from oauth.session import (
    create_session,
    validate_csrf_token,
    get_session_data,
    cleanup_oauth_session,
    validate_token_response,
    COOKIE_SECURE,
)
from oauth.user_data import extract_provider_user_data
from routers.users import find_or_create_user

router = APIRouter()


def _oauth_login(provider: OAuthProvider, callback_path: str, response: Response):
    """Generic OAuth login handler for any provider."""
    redirect_uri = f"http://localhost:8000{callback_path}"
    authorization_url, state, code_verifier = get_oauth_authorization_url(provider, redirect_uri)

    # Store session data
    create_session(state, code_verifier, redirect_uri)

    redirect_response = RedirectResponse(url=authorization_url, status_code=302)
    redirect_response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=600
    )
    return redirect_response


async def _oauth_callback(
    provider: OAuthProvider,
    code: str,
    state: str,
    oauth_state: str,
    response: Response,
    db: Session,
):
    """Generic OAuth callback handler for any provider."""
    # Validate CSRF token
    validate_csrf_token(state, oauth_state)
    
    # Retrieve session data
    code_verifier, redirect_uri = get_session_data(state)
    
    # Clean up session
    cleanup_oauth_session(state, response)
    
    # Exchange code for access token with PKCE
    token_response = await exchange_oauth_code_for_token(provider, code, redirect_uri, code_verifier)
    access_token = validate_token_response(token_response)
    
    # Fetch user info
    user_info = await get_oauth_user_info(provider, access_token)
    
    # Extract provider-specific user data
    username, email, fullname = await extract_provider_user_data(provider, user_info, access_token)
    
    # Find or create user in DB
    username = find_or_create_user(db, username, email, fullname)

    # Issue local JWT and redirect to frontend
    jwt_token = create_access_token(subject=username)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    redirect_url = f"{frontend_url}/oauth/callback?token={jwt_token}&username={username}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/github/login")
def github_login(response: Response):
    """Redirect user to GitHub OAuth consent screen."""
    return _oauth_login(OAuthProvider.GITHUB, "/auth/github/callback", response)


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    oauth_state: str = Cookie(None),
    response: Response = None,
    db: Session = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    try:
        return await _oauth_callback(OAuthProvider.GITHUB, code, state, oauth_state, response, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/login")
def google_login(response: Response):
    """Redirect user to Google OAuth consent screen."""
    return _oauth_login(OAuthProvider.GOOGLE, "/auth/google/callback", response)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state: str = Cookie(None),
    response: Response = None,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback."""
    try:
        return await _oauth_callback(OAuthProvider.GOOGLE, code, state, oauth_state, response, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))