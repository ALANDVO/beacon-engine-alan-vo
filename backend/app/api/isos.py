from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import os
import aiofiles

from app.core.config import get_settings
from app.core.database import get_db
from app.core.db_utils import execute, scalar, scalars, commit, refresh, add, delete
from app.core.iso_parser import extract_iso_metadata, ISOParserError, ISOMetadata
from app.models import ISOImage
from app.schemas import (
    ISOImageResponse,
    ISOImageCreate,
    PaginatedResponse,
    ErrorResponse,
)
from app.api.users import get_current_user

router = APIRouter()


def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def compute_sha256_async(file_path: str) -> str:
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


@router.post("", response_model=ISOImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_iso(
    file: UploadFile = File(...),
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> ISOImageResponse:
    settings = get_settings()
    upload_dir = os.path.join(settings.build_workspace, "isos", user.id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(8192):
            await f.write(chunk)

    file_size = os.path.getsize(file_path)
    sha256 = await compute_sha256_async(file_path)

    # Extract metadata from ISO
    metadata = ISOMetadata()
    try:
        metadata = await extract_iso_metadata(file_path)
    except ISOParserError:
        # Metadata extraction failed, continue with empty metadata
        pass

    existing = await execute(
        db,
        select(ISOImage).where(ISOImage.sha256 == sha256, ISOImage.owner_id == user.id),
    )
    if existing_iso := (await scalar(db, select(ISOImage).where(ISOImage.sha256 == sha256, ISOImage.owner_id == user.id))):
        os.remove(file_path)
        return ISOImageResponse.model_validate(existing_iso)

    iso = ISOImage(
        owner_id=user.id,
        filename=file.filename,
        sha256=sha256,
        size_bytes=file_size,
        storage_path=file_path,
        version=metadata.version,
        edition=metadata.edition,
        build_number=metadata.build_number,
        architecture=metadata.architecture,
        language=metadata.language,
    )
    await add(db, iso)
    await commit(db)
    await refresh(db, iso)
    return ISOImageResponse.model_validate(iso)


@router.get("", response_model=PaginatedResponse)
async def list_isos(
    page: int = 1,
    page_size: int = 20,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    query = select(ISOImage).where(ISOImage.owner_id == user.id).order_by(ISOImage.created_at.desc())
    total = await scalar(db, select(func.count()).select_from(query.subquery()))
    total = total or 0

    offset = (page - 1) * page_size
    items = await scalars(db, query.offset(offset).limit(page_size))

    return PaginatedResponse(
        items=[ISOImageResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{iso_id}", response_model=ISOImageResponse)
async def get_iso(
    iso_id: str,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> ISOImageResponse:
    iso = await scalar(
        db,
        select(ISOImage).where(ISOImage.id == iso_id, ISOImage.owner_id == user.id),
    )
    if not iso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ISO not found")
    return ISOImageResponse.model_validate(iso)


@router.delete("/{iso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iso(
    iso_id: str,
    user: ISOImage = Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> None:
    iso = await scalar(
        db,
        select(ISOImage).where(ISOImage.id == iso_id, ISOImage.owner_id == user.id),
    )
    if not iso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ISO not found")

    if os.path.exists(iso.storage_path):
        os.remove(iso.storage_path)

    await delete(db, iso)
    await commit(db)