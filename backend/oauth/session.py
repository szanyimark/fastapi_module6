"""OAuth session management - now uses Redis."""

import os
from fastapi import Response

from oauth.redis_session import (
    create_session,
    get_session_data,
    delete_session,
    validate_csrf_token,
    validate_token_response,
)

# Get cookie security setting from env (True for HTTPS/production, False for local dev)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def cleanup_oauth_session(state: str, response: Response) -> None:
    """Remove OAuth session data and state cookie."""
    delete_session(state)
    response.delete_cookie("oauth_state")