import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Tests ke liye alag in-memory database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


client = TestClient(app)


def test_health_check():
    assert client.get("/").json()["status"] == "ok"


def test_create_and_get_task():
    res = client.post("/tasks/", json={"title": "Learn FastAPI"})
    assert res.status_code == 201
    task_id = res.json()["id"]
    assert client.get(f"/tasks/{task_id}").json()["title"] == "Learn FastAPI"


def test_validation_error_on_empty_title():
    res = client.post("/tasks/", json={"title": ""})
    assert res.status_code == 422


def test_update_task():
    task_id = client.post("/tasks/", json={"title": "Test"}).json()["id"]
    res = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert res.json()["completed"] is True


def test_filter_completed():
    client.post("/tasks/", json={"title": "A"})
    done_id = client.post("/tasks/", json={"title": "B"}).json()["id"]
    client.patch(f"/tasks/{done_id}", json={"completed": True})
    res = client.get("/tasks/", params={"completed": True})
    assert len(res.json()) == 1


def test_delete_task():
    task_id = client.post("/tasks/", json={"title": "Bye"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404
