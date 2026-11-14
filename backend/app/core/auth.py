from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException, status
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
    """Create a JWT access token."""
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


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return its payload."""
    secret = settings.auth_secret or "dev-secret"
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        # Ensure required fields
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
