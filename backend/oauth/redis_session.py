"""Redis-based OAuth session management."""

import os
import json
import redis
from typing import Tuple, Optional
from fastapi import HTTPException

# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
SESSION_TTL = 600  # 10 minutes (same as cookie max_age)

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
    return _redis_client


def create_session(state: str, code_verifier: str, redirect_uri: str) -> None:
    """Store OAuth session data in Redis."""
    redis_client = get_redis()
    session_data = json.dumps({
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri
    })
    redis_client.setex(f"oauth_session:{state}", SESSION_TTL, session_data)


def get_session_data(state: str) -> Tuple[str, str]:
    """Retrieve OAuth session data from Redis."""
    redis_client = get_redis()
    session_data = redis_client.get(f"oauth_session:{state}")
    
    if not session_data:
        raise HTTPException(
            status_code=400, 
            detail="Session expired or invalid"
        )
    
    data = json.loads(session_data)
    return data["code_verifier"], data["redirect_uri"]


def delete_session(state: str) -> None:
    """Remove OAuth session from Redis."""
    redis_client = get_redis()
    redis_client.delete(f"oauth_session:{state}")


def validate_csrf_token(state: str, oauth_state: str) -> None:
    """Validate state parameter matches cookie to prevent CSRF attacks."""
    if not state or state != oauth_state:
        raise HTTPException(
            status_code=400, 
            detail="Invalid state parameter - possible CSRF attack"
        )


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