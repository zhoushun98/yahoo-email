import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Admin, YahooAccount, Alias
from database import get_db
from auth import hash_password, create_session_cookie
from routers.admin import router as admin_router

app = FastAPI()
app.include_router(admin_router)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 预创建管理员
    db = TestSession()
    admin = Admin(username="admin", password_hash=hash_password("admin123"))
    db.add(admin)
    db.commit()
    db.close()

    yield TestClient(app, follow_redirects=False)
    app.dependency_overrides.clear()
    engine.dispose()


def _auth_cookie() -> dict:
    cookie = create_session_cookie("admin")
    return {"cookies": {"session": cookie}}


def test_login_success(client):
    resp = client.post("/admin/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 303
    assert "session" in resp.cookies


def test_login_failure(client):
    resp = client.post("/admin/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 200  # 重新渲染登录页
    assert "session" not in resp.cookies


def test_add_account(client):
    cookie = create_session_cookie("admin")
    resp = client.post(
        "/admin/accounts",
        data={"email": "test@yahoo.com", "imap_password": "secret"},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303


def test_add_alias_batch(client):
    cookie = create_session_cookie("admin")
    # 先添加账号
    client.post(
        "/admin/accounts",
        data={"email": "test@yahoo.com", "imap_password": "secret"},
        cookies={"session": cookie},
    )
    # 批量添加别名（一行一个）
    resp = client.post(
        "/admin/aliases",
        data={"alias_emails": "a1@yahoo.com\na2@yahoo.com\na3@yahoo.com", "account_id": "1"},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303


def test_unauthenticated_access_redirects(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/admin/login" in resp.headers["location"]
