from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, YahooAccount, Alias
from database import get_db
from encryption import encrypt_password
from routers.mail import router as mail_router

app = FastAPI()
app.include_router(mail_router)


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

    # 预创建账号和别名
    db = TestSession()
    account = YahooAccount(email="main@yahoo.com", imap_password=encrypt_password("secret"))
    db.add(account)
    db.commit()
    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id, enabled=True)
    disabled_alias = Alias(alias_email="disabled@yahoo.com", account_id=account.id, enabled=False)
    db.add_all([alias, disabled_alias])
    db.commit()
    db.close()

    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@patch("routers.mail.fetch_emails")
def test_fetch_mail_success(mock_fetch, client):
    mock_fetch.return_value = [
        {"from": "sender@test.com", "subject": "验证码", "date": "Mon, 14 Apr 2026", "snippet": "123456"}
    ]
    resp = client.post("/api/mail/fetch", json={"alias_email": "alias1@yahoo.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["emails"]) == 1
    assert data["emails"][0]["subject"] == "验证码"


def test_fetch_mail_alias_not_found(client):
    resp = client.post("/api/mail/fetch", json={"alias_email": "nonexist@yahoo.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "未找到" in data["error"]


def test_fetch_mail_disabled_alias(client):
    resp = client.post("/api/mail/fetch", json={"alias_email": "disabled@yahoo.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "未找到" in data["error"]


@patch("routers.mail.fetch_emails")
def test_fetch_mail_imap_failure(mock_fetch, client):
    mock_fetch.return_value = None
    resp = client.post("/api/mail/fetch", json={"alias_email": "alias1@yahoo.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "不可用" in data["error"]
