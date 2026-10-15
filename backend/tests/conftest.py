import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import User, UserRole


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield test_db

    app = create_app(testing=True)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def demo_user() -> User:
    return User(
        id="demo-user",
        email="demo@local",
        name="Demo User",
        roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER],
    )


@pytest.fixture(autouse=True)
def settings_override(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("BUILD_WORKSPACE", "./test_data/builds")