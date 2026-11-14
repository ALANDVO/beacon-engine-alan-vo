from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.db_utils import commit, refresh
from app.core.auth import create_access_token, verify_access_token
from app.models import User, UserRole
from app.schemas import UserResponse, UserUpdate

router = APIRouter()

DEMO_USER_ID = "demo-user"


async def get_current_user(request: Request, db: Session | AsyncSession = Depends(get_db)) -> User:
    settings = get_settings()
    # Try to verify token from cookie if present
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = verify_access_token(token)
            # Build User object from token payload
            return User(
                id=payload.get("sub", DEMO_USER_ID),
                email=payload.get("email", "demo@local"),
                name=payload.get("name", "Demo User"),
                roles=[UserRole(role) for role in payload.get("roles", ["viewer"])],
                created_at=None,  # Not provided in token
                updated_at=None,
            )
        except HTTPException:
            # Invalid token; fall through to demo mode
            pass

    # Fallback to demo mode if enabled
    if settings.demo_mode:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return User(
            id=DEMO_USER_ID,
            email="demo@local",
            name="Demo User",
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER],
            created_at=now,
            updated_at=now,
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Enable demo_mode for local development.",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> UserResponse:
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.avatar_url is not None:
        user.avatar_url = user_update.avatar_url
    if user_update.roles is not None:
        user.roles = user_update.roles
    # Only persist if not in demo_mode
    settings = get_settings()
    if not settings.demo_mode:
        await commit(db)
        await refresh(db, user)
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
            max_age=3600 * 24 * 7,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
        )
        return {"message": "Logged in demo user"}
    # In non-demo mode, we could redirect to OIDC; for now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OIDC login not implemented in this round",
    )


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}
