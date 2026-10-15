from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.core.db_utils import execute, scalar, scalars, commit, refresh, add, delete
from app.models import BuildRecipe
from app.schemas import (
    BuildRecipeCreate,
    BuildRecipeResponse,
    BuildRecipeUpdate,
    PaginatedResponse,
    ErrorResponse,
)
from app.api.users import get_current_user

router = APIRouter()


def validate_recipe_json(recipe_json: str) -> dict:
    try:
        data = json.loads(recipe_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {e}")

    required_keys = ["components", "removals", "registry_tweaks", "unattend_snippets"]
    for key in required_keys:
        if key not in data:
            data[key] = []
    return data


@router.post("", response_model=BuildRecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_in: BuildRecipeCreate,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildRecipeResponse:
    validated = validate_recipe_json(recipe_in.recipe_json)

    existing = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.owner_id == user.id, BuildRecipe.name == recipe_in.name),
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recipe name already exists")

    recipe = BuildRecipe(
        owner_id=user.id,
        name=recipe_in.name,
        description=recipe_in.description,
        recipe_json=json.dumps(validated),
    )
    await add(db, recipe)
    await commit(db)
    await refresh(db, recipe)
    return BuildRecipeResponse.model_validate(recipe)


@router.get("", response_model=PaginatedResponse)
async def list_recipes(
    page: int = 1,
    page_size: int = 20,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    query = select(BuildRecipe).where(BuildRecipe.owner_id == user.id).order_by(BuildRecipe.updated_at.desc())
    total = await scalar(db, select(func.count()).select_from(query.subquery()))
    total = total or 0

    offset = (page - 1) * page_size
    items = await scalars(db, query.offset(offset).limit(page_size))

    return PaginatedResponse(
        items=[BuildRecipeResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{recipe_id}", response_model=BuildRecipeResponse)
async def get_recipe(
    recipe_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildRecipeResponse:
    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return BuildRecipeResponse.model_validate(recipe)


@router.patch("/{recipe_id}", response_model=BuildRecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: BuildRecipeUpdate,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildRecipeResponse:
    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    if recipe_update.name is not None:
        existing = await scalar(
            db,
            select(BuildRecipe).where(
                BuildRecipe.owner_id == user.id,
                BuildRecipe.name == recipe_update.name,
                BuildRecipe.id != recipe_id,
            ),
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recipe name already exists")
        recipe.name = recipe_update.name

    if recipe_update.description is not None:
        recipe.description = recipe_update.description

    if recipe_update.recipe_json is not None:
        validated = validate_recipe_json(recipe_update.recipe_json)
        recipe.recipe_json = json.dumps(validated)
        recipe.version += 1

    await commit(db)
    await refresh(db, recipe)
    return BuildRecipeResponse.model_validate(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> None:
    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    await delete(db, recipe)
    await commit(db)


@router.post("/{recipe_id}/clone", response_model=BuildRecipeResponse, status_code=status.HTTP_201_CREATED)
async def clone_recipe(
    recipe_id: str,
    user=Depends(get_current_user),
    db: Session | AsyncSession = Depends(get_db),
) -> BuildRecipeResponse:
    recipe = await scalar(
        db,
        select(BuildRecipe).where(BuildRecipe.id == recipe_id, BuildRecipe.owner_id == user.id),
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    new_name = f"{recipe.name} (copy)"
    counter = 1
    while True:
        existing = await scalar(
            db,
            select(BuildRecipe).where(BuildRecipe.owner_id == user.id, BuildRecipe.name == new_name),
        )
        if not existing:
            break
        counter += 1
        new_name = f"{recipe.name} (copy {counter})"

    new_recipe = BuildRecipe(
        owner_id=user.id,
        name=new_name,
        description=recipe.description,
        recipe_json=recipe.recipe_json,
    )
    await add(db, new_recipe)
    await commit(db)
    await refresh(db, new_recipe)
    return BuildRecipeResponse.model_validate(new_recipe)