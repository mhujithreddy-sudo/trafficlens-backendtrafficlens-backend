"""
Pytest fixtures and test configuration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.config import settings

# Test database
TEST_DATABASE_URL = "sqlite:///./test_trafficlens.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before tests and drop after."""
    import app.models.device  # noqa
    import app.models.traffic  # noqa
    import app.models.bandwidth  # noqa
    import app.models.service  # noqa
    import app.models.alert  # noqa

    Base.metadata.create_all(bind=test_engine)
    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield

    Base.metadata.drop_all(bind=test_engine)
    import os
    if os.path.exists("./test_trafficlens.db"):
        try:
            os.remove("./test_trafficlens.db")
        except Exception:
            pass


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(fastapi_app) as test_client:
        yield test_client
