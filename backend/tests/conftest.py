import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.config import Base
from backend.main import app
from backend.database.config import get_db
from backend.models.user import User
from backend.core.security import hash_password, create_access_token
from backend.core.security import create_access_token

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db):
    user_data = {
        "email": "delivered@resend.dev",
        "password": "testpass123",
        "name": "Test User",
        "is_verified": True
    }
    
    hashed_password = hash_password(user_data["password"])
    user = User(
        email=user_data["email"],
        password=hashed_password,
        name=user_data["name"],
        is_verified=user_data["is_verified"]
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    user_data["id"] = user.id
    return user_data

@pytest.fixture(scope="function")
def test_user_token(test_user):
    return create_access_token(data={"sub": test_user["email"]})

@pytest.fixture(scope="function")
def authorized_client(client, test_user_token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}"
    }
    return client 