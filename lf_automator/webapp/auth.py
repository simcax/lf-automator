"""Authentication module for the web dashboard."""

import os
from functools import wraps
from typing import Callable

from flask import redirect, session, url_for


def check_access_key(provided_key: str) -> bool:
    """Validate the provided access key against the configured ACCESS_KEY.

    Args:
        provided_key: The access key provided by the user

    Returns:
        bool: True if the provided key matches the configured ACCESS_KEY, False otherwise
    """
    configured_key = os.environ.get("ACCESS_KEY", "")
    return provided_key == configured_key and configured_key != ""


def require_auth(f: Callable) -> Callable:
    """Decorator for protected routes that require authentication.

    Checks the session for authentication status and redirects to login
    if not authenticated. Allows access if authenticated.

    Args:
        f: The route function to protect

    Returns:
        Callable: Wrapped function with authentication check
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated", False):
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)

    return decorated_function


def set_authenticated(authenticated: bool) -> None:
    """Set the authentication status in the session.

    Args:
        authenticated: Boolean flag indicating authentication status
    """
    session["authenticated"] = authenticated


def clear_session() -> None:
    """Clear all session data."""
    session.clear()


def is_authenticated() -> bool:
    """Check if the current session is authenticated.

    Returns:
        bool: True if authenticated, False otherwise
    """
    return session.get("authenticated", False)
