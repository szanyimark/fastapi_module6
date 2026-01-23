"""OAuth session management and CSRF protection utilities."""

import os
from typing import Dict, Tuple

from fastapi import HTTPException, Response

# In-memory storage for state and code_verifier (use Redis/DB in production)
oauth_sessions: Dict[str, Dict[str, str]] = {}

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


def get_session_data(state: str) -> Tuple[str, str]:
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