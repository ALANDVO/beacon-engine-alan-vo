from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.db_utils import execute
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check(db: Session | AsyncSession = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    # Verify database connectivity
    await execute(db, text("SELECT 1"))
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )