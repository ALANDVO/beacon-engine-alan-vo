from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


class UserRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: str
    name: str
    avatar_url: Optional[str] = None
    roles: list[UserRole] = [UserRole.VIEWER]


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: Optional[list[UserRole]] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ISOImageBase(BaseModel):
    filename: str
    sha256: str
    size_bytes: int
    version: Optional[str] = None
    edition: Optional[str] = None
    build_number: Optional[int] = None
    architecture: Optional[str] = None
    language: Optional[str] = None


class ISOImageCreate(ISOImageBase):
    storage_path: str


class ISOImageResponse(ISOImageBase):
    id: str
    owner_id: str
    storage_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildRecipeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    recipe_json: str


class BuildRecipeCreate(BuildRecipeBase):
    pass


class BuildRecipeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    recipe_json: Optional[str] = None
    version: Optional[int] = None


class BuildRecipeResponse(BuildRecipeBase):
    id: str
    owner_id: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildStage(str, Enum):
    PENDING = "pending"
    MOUNTING = "mounting"
    INVENTORY = "inventory"
    COMPONENT_CLEANUP = "component_cleanup"
    REGISTRY_TWEAKS = "registry_tweaks"
    UNMOUNTING = "unmounting"
    ISO_CREATION = "iso_creation"
    COMPLETED = "completed"
    FAILED = "failed"


class BuildJobBase(BaseModel):
    iso_id: str
    recipe_id: str


class BuildJobCreate(BuildJobBase):
    pass


class BuildJobResponse(BaseModel):
    id: str
    owner_id: str
    iso_id: str
    recipe_id: str
    stage: BuildStage
    progress: int
    status_message: Optional[str] = None
    error_message: Optional[str] = None
    log_path: Optional[str] = None
    output_iso_path: Optional[str] = None
    output_iso_sha256: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildLogEntry(BaseModel):
    id: str
    job_id: str
    stage: BuildStage
    timestamp: datetime
    level: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class BuildLogResponse(BaseModel):
    logs: list[BuildLogEntry]
    total: int


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorResponse(BaseModel):
    detail: list[dict[str, Any]]