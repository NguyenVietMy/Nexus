"""JWT-based authentication middleware for FastAPI service layer.

Provides:
  - AuthMiddleware class: validates JWT tokens, checks roles/permissions
  - require_auth decorator: protects service functions with token validation
"""

import functools
import logging
from datetime import datetime, timezone
from typing import Any, Callable

import jwt
from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Stateless JWT authentication handler.

    Usage:
        auth = AuthMiddleware()
        payload = auth.validate_token(token)
        auth.check_permissions(payload, required=["read", "write"])
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        issuer: str | None = None,
    ) -> None:
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.issuer = issuer or settings.jwt_issuer

    # ------------------------------------------------------------------
    # Token operations
    # ------------------------------------------------------------------

    def validate_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token.

        Raises HTTPException(401) on invalid/expired tokens.
        Returns the decoded payload dict.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer if self.issuer else None,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    def check_permissions(
        self, payload: dict[str, Any], required: list[str]
    ) -> None:
        """Verify that the token payload contains the required permissions.

        Raises HTTPException(403) if any required permission is missing.
        """
        token_permissions: list[str] = payload.get("permissions", [])
        missing = [p for p in required if p not in token_permissions]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing)}",
            )

    def extract_token(self, request: Request) -> str:
        """Extract the Bearer token from the Authorization header.

        Raises HTTPException(401) if the header is missing or malformed.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")
        return auth_header[7:]

    # ------------------------------------------------------------------
    # Convenience: authenticate a request end-to-end
    # ------------------------------------------------------------------

    def authenticate(
        self, request: Request, required_permissions: list[str] | None = None
    ) -> dict[str, Any]:
        """Full auth flow: extract token → validate → check permissions.

        Returns the decoded JWT payload.
        """
        token = self.extract_token(request)
        payload = self.validate_token(token)
        if required_permissions:
            self.check_permissions(payload, required_permissions)
        return payload


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_auth = AuthMiddleware()


def require_auth(
    permissions: list[str] | None = None,
) -> Callable:
    """Decorator for service functions that require authentication.

    The decorated function must accept a `request: Request` keyword argument
    (or have it injected via FastAPI dependency injection).

    Example:
        @require_auth(permissions=["write"])
        async def create_item(request: Request, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request | None = kwargs.get("request")
            if request is None:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized",
                )
            _auth.authenticate(request, required_permissions=permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
