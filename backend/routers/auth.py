import os
import secrets
from fastapi import APIRouter, HTTPException, Cookie, Response, Depends
from fastapi.responses import RedirectResponse
from oauth import (
    get_oauth_authorization_url,
    exchange_oauth_code_for_token,
    get_oauth_user_info,
    get_oauth_user_emails,
)
from oauth.providers import OAuthProvider
from utils import create_access_token, hash_password
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User

router = APIRouter()

# In-memory storage for state and code_verifier (use Redis/DB in production)
oauth_sessions = {}

# Get cookie security setting from env (True for HTTPS/production, False for local dev)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def create_session(state: str, code_verifier: str, redirect_uri: str) -> None:
    """Store OAuth session data for later validation."""
    oauth_sessions[state] = {
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri
    }


def validate_csrf_token(state: str, oauth_state: str) -> None:
    """Validate state parameter matches cookie to prevent CSRF attacks."""
    if not state or state != oauth_state:
        raise HTTPException(
            status_code=400, 
            detail="Invalid state parameter - possible CSRF attack"
        )


def get_session_data(state: str) -> tuple[str, str]:
    """Retrieve and validate OAuth session data."""
    session_data = oauth_sessions.get(state)
    if not session_data:
        raise HTTPException(
            status_code=400, 
            detail="Session expired or invalid"
        )
    return session_data["code_verifier"], session_data["redirect_uri"]


def cleanup_oauth_session(state: str, response: Response) -> None:
    """Remove OAuth session data and state cookie."""
    if state in oauth_sessions:
        del oauth_sessions[state]
    response.delete_cookie("oauth_state")


def validate_token_response(token_response: dict) -> str:
    """Validate token response and extract access token."""
    if "error" in token_response:
        raise HTTPException(
            status_code=400,
            detail=token_response.get("error_description", "OAuth error")
        )
    
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")
    
    return access_token


async def extract_github_user_data(user_info: dict, access_token: str) -> tuple[str, str, str]:
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


def extract_google_user_data(user_info: dict) -> tuple[str, str, str]:
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
) -> tuple[str, str, str]:
    """Extract user data based on OAuth provider."""
    if provider == OAuthProvider.GITHUB:
        return await extract_github_user_data(user_info, access_token)
    elif provider == OAuthProvider.GOOGLE:
        return extract_google_user_data(user_info)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")


def find_or_create_user(
    db: Session,
    username: str,
    email: str,
    fullname: str
) -> str:
    """Find existing user or create new one. Returns the username."""
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing:
        return existing.username
    
    # Create new user with random password (OAuth users don't use password)
    random_pw = secrets.token_urlsafe(32)
    new_user = User(
        username=username,
        fullname=fullname,
        email=email,
        hashed_password=hash_password(random_pw),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user.username


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