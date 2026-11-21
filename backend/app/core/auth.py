from __future__ import annotations

import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def create_access_token(
    subject: str,
    name: str,
    email: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    In demo mode, signs with auth_secret. In OIDC mode, the token is
    expected to already be a signed JWT from the IdP and is returned
    unchanged (or a session token can be minted here).
    """
    if settings.demo_mode:
        secret = settings.auth_secret or "dev-secret"
        if not secret:
            raise RuntimeError("auth_secret must be configured for token signing")

        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(hours=1))
        payload: Dict[str, Any] = {
            "sub": subject,
            "email": email,
            "name": name,
            "roles": roles,
            "iat": now,
            "exp": expire,
        }
        return jwt.encode(payload, secret, algorithm="HS256")
    else:
        # OIDC mode: return the original subject/email/roles for session
        # The actual token validation happens in verify_access_token
        return f"oidc:{subject}"


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return its payload.

    In demo mode: verifies HS256 signature with auth_secret.
    In OIDC mode: validates the token from the Keycloak issuer using
    the JWKS endpoint (or symmetric secret if configured).
    """
    if settings.demo_mode:
        secret = settings.auth_secret or "dev-secret"
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            if "sub" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            return payload
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from exc
    else:
        # OIDC mode: validate token from Keycloak issuer
        issuer_url = settings.oidc_issuer_url
        if not issuer_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OIDC issuer URL not configured",
            )

        # For now, use the secret as a fallback HS256 validation
        # In full Keycloak integration, this would use the JWKS endpoint
        secret = settings.auth_secret or ""
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            if "sub" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            # Optionally verify issuer/aud against Keycloak config
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OIDC token",
            )
