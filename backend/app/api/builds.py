
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.db_utils import execute, scalar, scalars, commit, refresh, add, delete
from app.models import BuildJob, BuildStage, ISOImage, BuildRecipe, BuildLog
from app.schemas import (
    BuildJobCreate,
    BuildJobResponse,
    BuildLogEntry,
    BuildLogResponse,
    PaginatedResponse,
)
from app.api.users import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=BuildJobResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build: BuildJobCreate,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildJobResponse:
    iso = await scalar(
        db,
        select(ISOImage).where(ISOImage.id == build.iso_id, ISOImage.owner_id == user.id),
    )
    if not iso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ISO not found")

    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == build.recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    job = BuildJob(
        owner_id=user.id,
        iso_id=iso.id,
        recipe_id=recipe.id,
        stage=BuildStage.PENDING,
        
    )
    await add(db, job)
    await commit(db)
    await refresh(db, job)
    logger.info("Created build job: %s (id=%s, iso=%s, recipe=%s)", job.id, job.id, iso.filename, recipe.name)

    # Log initial stage
    log_entry = BuildLog(
        job_id=job.id,
        stage=BuildStage.PENDING,
        level="info",
        message="Build job created",
        
    )
    await add(db, log_entry)
    await commit(db)

    return BuildJobResponse.model_validate(job)


@router.get("", response_model=PaginatedResponse)
async def list_builds(
    page: int = 1,
    page_size: int = 20,
    stage: BuildStage | None = None,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    query = select(BuildJob).where(BuildJob.owner_id == user.id).order_by(BuildJob.created_at.desc())
    if stage:
        query = query.where(BuildJob.stage == stage)
    total = await scalar(db, select(func.count()).select_from(query.subquery()))
    total_pages = (total + page_size - 1) // page_size
    items = await scalars(db, query.offset((page - 1) * page_size).limit(page_size))
    logger.info("Listed %d builds for user %s", len(items), user.id)
    return PaginatedResponse(
        items=[BuildJobResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{build_id}", response_model=BuildJobResponse)
async def get_build(
    build_id: str,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildJobResponse:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")
    logger.info("Retrieved build %s (id=%s)", build_id, job.id)
    return BuildJobResponse.model_validate(job)


@router.get("/{build_id}/logs", response_model=BuildLogResponse)
async def get_build_logs(
    build_id: str,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildLogResponse:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

    logs = await scalars(
        db,
        select(BuildLog).where(BuildLog.job_id == build_id).order_by(BuildLog.timestamp.asc()),
    )
    return BuildLogResponse(
        logs=[BuildLogEntry.model_validate(log) for log in logs],
        total=len(logs),
    )


@router.delete("/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_build(
    build_id: str,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> None:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

    await delete(db, job)
    await commit(db)
    logger.info("Deleted build %s (id=%s)", build_id, job.id)

