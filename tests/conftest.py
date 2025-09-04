"""
Test configuration and fixtures for tic-tac-toe backend tests
"""

from dotenv import load_dotenv
from models.base import Base
from server import app
from db import db as get_db
import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# Test database URL - with fallback for JSONB compatibility

load_dotenv()

# Try PostgreSQL first for JSONB support, fallback to SQLite with JSON as TEXT
try:
    # Use PostgreSQL test database for full JSONB compatibility
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_pass@localhost:5432/test_tic_tac_toe"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection
    engine.connect().close()
    print("Using PostgreSQL for tests (full JSONB support)")
except Exception:
    # Fallback to SQLite in-memory for CI/development environments
    print("PostgreSQL not available, using SQLite for tests (JSONB as TEXT)")
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Monkey patch JSONB to TEXT for SQLite compatibility
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import Text

    def visit_JSONB(self, type_, **kw):
        return self.visit_TEXT(Text(), **kw)

    SQLiteTypeCompiler.visit_JSONB = visit_JSONB

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}

        def setex(self, key, ttl, value):
            self.data[key] = value

        def get(self, key):
            return self.data.get(key)

        def ping(self):
            return True

    return MockRedis()
