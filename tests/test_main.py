import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base
from database import get_db
from main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 初始化管理员
    from auth import hash_password
    from models import Admin
    db = TestSession()
    admin = Admin(username="admin", password_hash=hash_password("admin123"))
    db.add(admin)
    db.commit()
    db.close()

    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Yahoo" in resp.text
    assert "拉取邮件" in resp.text


def test_admin_login_page(client):
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    assert "管理员登录" in resp.text


def test_admin_login_and_access(client):
    # 登录
    resp = client.post("/admin/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert resp.status_code == 303
    session_cookie = resp.cookies.get("session")
    assert session_cookie

    # 访问后台
    resp = client.get("/admin/", cookies={"session": session_cookie})
    assert resp.status_code == 200
    assert "管理后台" in resp.text
