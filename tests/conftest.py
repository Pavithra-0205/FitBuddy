import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

TEST_DB = Path("test_fitbuddy.db")
if TEST_DB.exists(): TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.resolve()}"
os.environ["ALLOW_AI_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()
from app.database import init_db, SessionLocal
from app.models import User, WorkoutPlan
from app.main import app
init_db()

@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(WorkoutPlan).delete(); db.query(User).delete(); db.commit(); db.close()
    yield
