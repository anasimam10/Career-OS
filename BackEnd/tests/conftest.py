"""
Shared test fixtures.
All tests use an in-memory SQLite database so nothing persists between runs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from database import get_db
from main import app

# In-memory SQLite for tests
TEST_DB_URL = "sqlite:///:memory:"

# StaticPool: ONE shared connection across threads, so the TestClient's app
# thread and the test thread see the same in-memory database. Without it,
# SQLite's default thread-local pooling gives the app thread a separate
# (empty) in-memory database for sessions not yet connected in the main thread.
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for in-memory SQLite
@event.listens_for(engine, "connect")
def _set_test_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Yield a clean database session with all tables created."""
    # Import models so metadata knows about them
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Yield a FastAPI TestClient with the DB session overridden."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
