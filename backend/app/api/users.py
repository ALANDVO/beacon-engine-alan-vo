from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.core.auth import create_access_token, verify_access_token
from app.models import User, UserRole
from app.schemas import UserResponse, UserUpdate

router = APIRouter()

DEMO_USER_ID = "demo-user"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()

    # Try to verify token from cookie if present
    token = request.cookies.get("access_token")
    payload = None
    if token:
        try:
            payload = verify_access_token(token)
        except HTTPException:
            payload = None

    # If we have a valid payload, use it; otherwise fall back to demo mode
    if payload is not None:
        user_id: str = payload.get("sub") or payload.get("id") or DEMO_USER_ID
        email: str = payload.get("email", "demo@local")
        name: str = payload.get("name", "Demo User")
        roles_raw = payload.get("roles", [])
        # Normalise roles to UserRole enum list
        if isinstance(roles_raw, str):
            roles = [UserRole(r.strip()) for r in roles_raw.split(",") if r.strip()]
        elif isinstance(roles_raw, list):
            roles = [UserRole(r) if isinstance(r, str) else UserRole.VIEWER for r in roles_raw]
        else:
            roles = [UserRole.VIEWER]

        # Look up user in DB or create if missing
        from datetime import datetime, timezone

        result = db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=user_id,
                email=email,
                name=name,
                roles=roles,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)

        return user

    # Fallback to demo mode if enabled
    if settings.demo_mode:
        from datetime import datetime, timezone

        user = User(
            id=DEMO_USER_ID,
            email="demo@local",
            name="Demo User",
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    user: User = Depends(get_current_user),
) -> UserResponse:
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.roles is not None:
        user.roles = user_update.roles
    return UserResponse.model_validate(user)


@router.post("/login")
async def login(response: Response) -> dict:
    settings = get_settings()

    if settings.demo_mode:
        token = create_access_token(
            subject=settings.demo_user_id,
            name="Demo User",
            email="demo@local",
            roles=settings.demo_user_roles,
        )
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
        )
        return {"message": "Logged in via demo mode", "mode": "demo"}

    # OIDC mode: redirect to Keycloak auth server
    import urllib.parse

    issuer_url = settings.oidc_issuer_url
    client_id = settings.oidc_client_id
    redirect_uri = settings.oidc_redirect_uri
    scopes = " ".join(settings.oidc_scopes or ["openid", "profile", "email", "roles"])

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": urllib.parse.urlsafe_b64encode(
            f"{settings.app_name}:demo".encode()
        ).decode().rstrip("="),
    }

    # Build Keycloak authorization URL
    auth_url = f"{issuer_url}/protocol/openid-connect/auth?{urllib.parse.urlencode(auth_params)}"

    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        detail="Redirecting to Keycloak",
        headers={"Location": auth_url},
    )


@router.post("/logout")
async def logout(response: Response) -> dict:
    settings = get_settings()

    if settings.demo_mode:
        response.delete_cookie(key="access_token")
        return {"message": "Logged out via demo mode"}

    # OIDC mode: redirect to Keycloak logout
    issuer_url = settings.oidc_issuer_url
    if not issuer_url:
        response.delete_cookie(key="access_token")
        return {"message": "Logged out"}

    redirect_uri = settings.oidc_redirect_uri or "http://localhost:5173/"
    logout_url = f"{issuer_url}/protocol/openid-connect/logout?redirect_uri={urllib.parse.quote_plus(redirect_uri)}"

    raise HTTPException(
        status_code=307,
        detail="Redirecting to Keycloak logout",
        headers={"Location": logout_url},
    )

# OIDC callback endpoint - exchanges authorization code for tokens
@router.post("/auth/callback")
async def oidc_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """OIDC callback endpoint that exchanges the authorization code for tokens.

    Keycloak redirects here with a `code` parameter. We exchange it for
    an ID token and access token, validate the ID token using JWKS,
    and create/update the user in the database.
    """
    settings = get_settings()

    if settings.demo_mode:
        token = create_access_token(
            subject=settings.demo_user_id,
            name="Demo User",
            email="demo@local",
            roles=settings.demo_user_roles,
        )
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )
        return {"message": "Logged in via demo mode", "mode": "demo"}

    # OIDC mode: exchange authorization code for tokens
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    issuer_url = settings.oidc_issuer_url
    client_id = settings.oidc_client_id
    client_secret = settings.oidc_client_secret
    redirect_uri = settings.oidc_redirect_uri or "http://localhost:5173/api/v1/auth/callback"

    # Exchange code for tokens at Keycloak's token endpoint
    token_url = f"{issuer_url}/protocol/openid-connect/token"

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }

    if client_secret:
        token_data["client_secret"] = client_secret

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data, timeout=30)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {token_response.text}",
            )

        token_json = token_response.json()
        id_token = token_json.get("id_token")
        access_token = token_json.get("access_token")

    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ID token received from Keycloak",
        )

    # Validate the ID token using JWKS
    jwks_url = f"{issuer_url}/protocol/openid-connect/certs"
    async with httpx.AsyncClient() as client:
        jwks_response = await client.get(jwks_url, timeout=30)
        if jwks_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch JWKS from Keycloak",
            )
        jwks = jwks_response.json()

    # Validate the ID token
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer_url,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {str(e)}",
        )

    # Extract user info from the ID token
    sub: str = payload.get("sub")
    email: str = payload.get("email", "")
    name: str = payload.get("name", "Keycloak User")
    roles_raw = payload.get("realm_access", {}).get("roles", [])

    # Normalise roles to UserRole enum list
    if isinstance(roles_raw, str):
        roles = [UserRole(r.strip()) for r in roles_raw.split(",") if r.strip()]
    elif isinstance(roles_raw, list):
        roles = [
            UserRole(r) if isinstance(r, str) else UserRole.VIEWER
            for r in roles_raw
            if r in [e.value for e in UserRole]
        ]
    else:
        roles = [UserRole.VIEWER]

    # Look up user in DB or create if missing
    from datetime import datetime, timezone

    result = db.execute(select(User).where(User.id == sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=sub,
            email=email or f"{sub}@keycloak.local",
            name=name,
            roles=roles,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        # Update user info if changed
        if user.email != email:
            user.email = email or user.email
        if user.name != name:
            user.name = name
        user.roles = roles
        user.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    # Create access token for session
    token = create_access_token(
        subject=user.id,
        name=user.name,
        email=user.email,
        roles=user.roles,
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
    )

    return {
        "message": "OIDC login successful",
        "mode": "oidc",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "roles": [r.value for r in user.roles],
        },
    }
