import os
import pytest
from fastapi.testclient import TestClient

# Set environment to testing BEFORE importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["TEST_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_EXPIRATION_MINUTES"] = "60"
os.environ["SECRET_KEY"] = "testing-secret-key"

# Mock redis to avoid connection errors if used at import time?
# Redis is used in app/core/config.py default, but app startup might try to connect.
# We'll see.

from app.main import create_app
from app.core.database import Base, engine

@pytest.fixture(scope="module")
def client():
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating tables: {e}")

    app = create_app()
    with TestClient(app) as c:
        yield c
    
    # Drop tables
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
    
    # Remove db file
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass
