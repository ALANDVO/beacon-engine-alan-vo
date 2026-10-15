import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class BuildStage(str, enum.Enum):
    PENDING = "pending"
    MOUNTING = "mounting"
    INVENTORY = "inventory"
    COMPONENT_CLEANUP = "component_cleanup"
    REGISTRY_TWEAKS = "registry_tweaks"
    UNMOUNTING = "unmounting"
    ISO_CREATION = "iso_creation"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    roles: Mapped[list[UserRole]] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=[UserRole.VIEWER],
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    isos: Mapped[list["ISOImage"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    recipes: Mapped[list["BuildRecipe"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    builds: Mapped[list["BuildJob"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ISOImage(Base):
    __tablename__ = "iso_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)

    # Parsed metadata
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "26H2"
    edition: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "Pro", "Enterprise"
    build_number: Mapped[int | None] = mapped_column(nullable=True)  # e.g., 26300
    architecture: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "x64"
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)  # e.g., "en-US"

    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="isos")
    builds: Mapped[list["BuildJob"]] = relationship(back_populates="iso_image")


class BuildRecipe(Base):
    __tablename__ = "build_recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    # Recipe JSON: components, removals, registry tweaks, unattend snippets
    recipe_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="recipes")
    builds: Mapped[list["BuildJob"]] = relationship(back_populates="recipe")

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_recipe_owner_name"),
    )


class BuildJob(Base):
    __tablename__ = "build_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    iso_id: Mapped[str] = mapped_column(String(36), ForeignKey("iso_images.id", ondelete="CASCADE"), index=True, nullable=False)
    recipe_id: Mapped[str] = mapped_column(String(36), ForeignKey("build_recipes.id", ondelete="CASCADE"), index=True, nullable=False)

    stage: Mapped[BuildStage] = mapped_column(Enum(BuildStage, native_enum=False), default=BuildStage.PENDING, nullable=False, index=True)
    progress: Mapped[int] = mapped_column(default=0, nullable=False)  # 0-100
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    log_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_iso_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_iso_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="builds")
    iso_image: Mapped["ISOImage"] = relationship(back_populates="builds")
    recipe: Mapped["BuildRecipe"] = relationship(back_populates="builds")

    __table_args__ = (
        Index("ix_build_jobs_owner_stage", "owner_id", "stage"),
    )


class BuildLog(Base):
    __tablename__ = "build_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("build_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    stage: Mapped[BuildStage] = mapped_column(Enum(BuildStage, native_enum=False), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # debug, info, warning, error
    message: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_build_logs_job_timestamp", "job_id", "timestamp"),
    )