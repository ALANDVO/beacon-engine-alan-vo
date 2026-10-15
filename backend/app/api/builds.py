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

router = APIRouter()


@router.post("", response_model=BuildJobResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_in: BuildJobCreate,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildJobResponse:
    iso = await scalar(
        db,
        select(ISOImage).where(ISOImage.id == build_in.iso_id, ISOImage.owner_id == user.id),
    )
    if not iso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ISO not found")

    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == build_in.recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    job = BuildJob(
        owner_id=user.id,
        iso_id=build_in.iso_id,
        recipe_id=build_in.recipe_id,
        stage=BuildStage.PENDING,
        progress=0,
        status_message="Queued",
    )
    await add(db, job)
    await commit(db)
    await refresh(db, job)
    return BuildJobResponse.model_validate(job)


@router.get("", response_model=PaginatedResponse)
async def list_builds(
    page: int = 1,
    page_size: int = 20,
    stage: str | None = None,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    query = select(BuildJob).where(BuildJob.owner_id == user.id).order_by(BuildJob.created_at.desc())
    if stage:
        try:
            stage_enum = BuildStage(stage)
            query = query.where(BuildJob.stage == stage_enum)
        except ValueError:
            pass

    total = await scalar(db, select(func.count()).select_from(query.subquery()))
    total = total or 0

    offset = (page - 1) * page_size
    items = await scalars(db, query.offset(offset).limit(page_size))

    return PaginatedResponse(
        items=[BuildJobResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{build_id}", response_model=BuildJobResponse)
async def get_build(
    build_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildJobResponse:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build job not found")
    return BuildJobResponse.model_validate(job)


@router.get("/{build_id}/logs", response_model=BuildLogResponse)
async def get_build_logs(
    build_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildLogResponse:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build job not found")

    logs = await scalars(
        db,
        select(BuildLog).where(BuildLog.job_id == build_id).order_by(BuildLog.timestamp.asc()),
    )

    return BuildLogResponse(
        logs=[BuildLogEntry.model_validate(l) for l in logs],
        total=len(logs),
    )


@router.delete("/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_build(
    build_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> None:
    job = await scalar(
        db,
        select(BuildJob).where(BuildJob.id == build_id, BuildJob.owner_id == user.id),
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build job not found")

    await delete(db, job)
    await commit(db)