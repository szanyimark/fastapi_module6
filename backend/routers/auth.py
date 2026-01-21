import os
import secrets
from fastapi import APIRouter, HTTPException, Cookie, Response, Depends
from fastapi.responses import RedirectResponse
from oauth import (
    get_authorization_url,
    exchange_code_for_token,
    get_user_info,
    get_user_emails,
)
from utils import create_access_token, hash_password
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User

router = APIRouter()

# In-memory storage for state and code_verifier (use Redis/DB in production)
oauth_sessions = {}


@router.get("/github/login")
def github_login(response: Response):
    """Redirect user to GitHub OAuth consent screen with PKCE and state."""
    redirect_uri = "http://localhost:8000/auth/github/callback"
    authorization_url, state, code_verifier = get_authorization_url(redirect_uri)

    # Store state and code_verifier for validation (use secure session storage in production)
    oauth_sessions[state] = {
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri
    }

    # Prepare redirect response and set state cookie (HttpOnly, lax)
    redirect_response = RedirectResponse(url=authorization_url, status_code=302)
    redirect_response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=600  # 10 minutes
    )

    return redirect_response


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    oauth_state: str = Cookie(None),
    response: Response = None,
    db: Session = Depends(get_db),
):
    """Handle GitHub OAuth callback with state validation."""
    try:
        # Validate state parameter (CSRF protection)
        if not state or state != oauth_state:
            raise HTTPException(status_code=400, detail="Invalid state parameter - possible CSRF attack")
        
        # Retrieve session data
        session_data = oauth_sessions.get(state)
        if not session_data:
            raise HTTPException(status_code=400, detail="Session expired or invalid")
        
        code_verifier = session_data["code_verifier"]
        redirect_uri = session_data["redirect_uri"]
        
        # Clean up session
        del oauth_sessions[state]
        response.delete_cookie("oauth_state")
        
        # Exchange code for access token with PKCE
        token_response = await exchange_code_for_token(code, redirect_uri, code_verifier)
        
        if "error" in token_response:
            raise HTTPException(
                status_code=400,
                detail=token_response.get("error_description", "OAuth error")
            )
        
        access_token = token_response.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Fetch and validate user info from GitHub
        user_info = await get_user_info(access_token)
        
        if "login" not in user_info:
            raise HTTPException(status_code=400, detail="Failed to retrieve user information")
        
        # Determine email (primary verified if available)
        email = user_info.get("email")
        if not email:
            emails = await get_user_emails(access_token)
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = (primary or (emails[0] if emails else None) or {}).get("email")
            if not email:
                email = f"{user_info['login']}@users.noreply.github.com"

        # Upsert user in local DB
        existing = (
            db.query(User)
            .filter((User.username == user_info["login"]) | (User.email == email))
            .first()
        )
        if not existing:
            # Create with random password hash (OAuth users don't use password)
            random_pw = secrets.token_urlsafe(32)
            new_user = User(
                username=user_info["login"],
                fullname=user_info.get("name"),
                email=email,
                hashed_password=hash_password(random_pw),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

        # Issue local JWT and redirect to frontend
        jwt_token = create_access_token(subject=user_info["login"])  # use GitHub username as subject
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        redirect_url = f"{frontend_url}/oauth/callback?token={jwt_token}&username={user_info['login']}"
        return RedirectResponse(url=redirect_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
