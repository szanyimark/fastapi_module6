from enum import Enum


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GITHUB = "github"
    GOOGLE = "google"


PROVIDERS = {
    OAuthProvider.GITHUB: {
        "client_id_env": "GITHUB_CLIENT_ID",
        "client_secret_env": "GITHUB_CLIENT_SECRET",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_info_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "default_scope": "user:email",
        "extra_auth_params": {"allow_signup": "true"},
        "token_headers": {"Accept": "application/json"},
        "token_body_extra": {},
    },
    OAuthProvider.GOOGLE: {
        "client_id_env": "GOOGLE_CLIENT_ID",
        "client_secret_env": "GOOGLE_CLIENT_SECRET",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "emails_url": None,
        "default_scope": "openid email profile",
        "extra_auth_params": {"access_type": "offline", "prompt": "consent", "response_type": "code"},
        "token_headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "token_body_extra": {"grant_type": "authorization_code"},
    },
}
