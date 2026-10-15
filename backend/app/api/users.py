from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.db_utils import execute, commit, refresh, add, scalar
from app.models import User, UserRole
from app.schemas import (
    ErrorResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter()

DEMO_USER_ID = "demo-user"


async def get_current_user(db: Session | AsyncSession = Depends(get_db)) -> User:
    settings = get_settings()
    if settings.demo_mode:
        # In demo mode, return a static demo user without DB query
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
    settings = get_settings()
    if not settings.demo_mode:
        await commit(db)
        await refresh(db, user)
    return UserResponse.model_validate(user)