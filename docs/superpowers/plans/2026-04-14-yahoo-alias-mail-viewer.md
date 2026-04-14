# 雅虎别名邮箱查看器 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Web 应用，管理员配置雅虎主账号和别名，客户输入别名地址即可实时拉取并查看最新 10 封邮件。

**Architecture:** FastAPI SSR 应用，前台极简居中布局（客户输入别名 → 实时 IMAP 拉取 → 展示邮件列表），管理后台顶部 Tab 导航（主账号/别名 CRUD）。SQLite 存储配置数据，Fernet 加密 IMAP 密码，bcrypt 哈希管理员密码。

**Tech Stack:** FastAPI, Jinja2, Bootstrap 5, SQLAlchemy, cryptography(Fernet), itsdangerous, bcrypt, Python imaplib, uv, SQLite

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `pyproject.toml` | 项目元数据和依赖 |
| `.env` | SECRET_KEY, FERNET_KEY |
| `.gitignore` | 排除 .env, *.db, __pycache__ 等 |
| `config.py` | 从 .env 加载配置 |
| `encryption.py` | Fernet 加解密 IMAP 密码 |
| `database.py` | SQLAlchemy 引擎、会话、建表 |
| `models.py` | Admin, YahooAccount, Alias ORM 模型 |
| `auth.py` | 管理员 session cookie 认证 |
| `imap_client.py` | IMAP 连接、搜索、解析邮件 |
| `routers/admin.py` | 管理后台路由（登录、账号/别名 CRUD） |
| `routers/mail.py` | 前台邮件拉取 API |
| `templates/base.html` | Bootstrap 5 基础模板 |
| `templates/index.html` | 前台首页（极简居中） |
| `templates/login.html` | 管理员登录页 |
| `templates/admin.html` | 管理后台页（Tab 导航） |
| `main.py` | FastAPI 应用入口，挂载路由 |
| `tests/conftest.py` | 测试 fixtures（内存 SQLite、测试客户端） |
| `tests/test_encryption.py` | 加密模块测试 |
| `tests/test_models.py` | 模型测试 |
| `tests/test_auth.py` | 认证模块测试 |
| `tests/test_imap_client.py` | IMAP 客户端测试（mock） |
| `tests/test_admin.py` | 管理后台路由测试 |
| `tests/test_mail.py` | 前台邮件拉取路由测试 |

---

### Task 1: 项目脚手架 — 初始化、配置、加密

**Files:**
- Create: `pyproject.toml`
- Create: `.env`
- Create: `.gitignore`
- Create: `config.py`
- Create: `encryption.py`
- Create: `tests/__init__.py`
- Create: `tests/test_encryption.py`

- [ ] **Step 1: 初始化项目**

```bash
cd /Users/jason/IdeaProjects/yahoo-email
uv init --name yahoo-email --python 3.12
```

- [ ] **Step 2: 添加依赖**

```bash
uv add fastapi uvicorn jinja2 python-multipart sqlalchemy cryptography itsdangerous bcrypt python-dotenv
uv add --dev pytest httpx
```

- [ ] **Step 3: 创建 .gitignore**

写入 `.gitignore`：

```gitignore
.env
*.db
__pycache__/
*.pyc
.venv/
.superpowers/
```

- [ ] **Step 4: 创建 .env**

```bash
python3 -c "from cryptography.fernet import Fernet; print(f'FERNET_KEY={Fernet.generate_key().decode()}')"
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"
```

写入 `.env`（用上面生成的值）：

```
SECRET_KEY=<生成的值>
FERNET_KEY=<生成的值>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

- [ ] **Step 5: 编写 config.py**

```python
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
FERNET_KEY = os.environ["FERNET_KEY"]
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///yahoo_email.db")
IMAP_TIMEOUT = int(os.environ.get("IMAP_TIMEOUT", "10"))
```

- [ ] **Step 6: 编写加密测试**

写入 `tests/__init__.py`（空文件）。

写入 `tests/test_encryption.py`：

```python
from encryption import encrypt_password, decrypt_password


def test_encrypt_decrypt_roundtrip():
    password = "my_secret_imap_password"
    encrypted = encrypt_password(password)
    assert encrypted != password
    assert decrypt_password(encrypted) == password


def test_different_passwords_produce_different_ciphertexts():
    a = encrypt_password("password_a")
    b = encrypt_password("password_b")
    assert a != b
```

- [ ] **Step 7: 运行测试，确认失败**

```bash
uv run pytest tests/test_encryption.py -v
```

预期：FAIL — `ImportError: cannot import name 'encrypt_password' from 'encryption'`

- [ ] **Step 8: 编写 encryption.py**

```python
from cryptography.fernet import Fernet

import config

_fernet = Fernet(config.FERNET_KEY.encode())


def encrypt_password(plain: str) -> str:
    """加密 IMAP 密码，返回 base64 密文字符串。"""
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """解密 IMAP 密码，返回明文。"""
    return _fernet.decrypt(encrypted.encode()).decode()
```

- [ ] **Step 9: 运行测试，确认通过**

```bash
uv run pytest tests/test_encryption.py -v
```

预期：2 passed

- [ ] **Step 10: 提交**

```bash
git add pyproject.toml uv.lock .gitignore .python-version config.py encryption.py tests/
git commit -m "feat: 项目脚手架 — 初始化依赖、配置加载、Fernet 加密模块"
```

---

### Task 2: 数据库和 ORM 模型

**Files:**
- Create: `database.py`
- Create: `models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 编写模型测试**

写入 `tests/conftest.py`：

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
```

写入 `tests/test_models.py`：

```python
from models import Admin, YahooAccount, Alias


def test_create_admin(db_session):
    admin = Admin(username="admin", password_hash="hashed")
    db_session.add(admin)
    db_session.commit()
    assert db_session.query(Admin).count() == 1
    assert db_session.query(Admin).first().username == "admin"


def test_create_yahoo_account(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()
    assert db_session.query(YahooAccount).first().email == "user@yahoo.com"
    assert db_session.query(YahooAccount).first().status == "normal"


def test_create_alias_with_relationship(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()

    assert alias.account.email == "user@yahoo.com"
    assert len(account.aliases) == 1
    assert account.aliases[0].alias_email == "alias1@yahoo.com"


def test_alias_enabled_default_true(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()
    assert alias.enabled is True


def test_cascade_delete_account_removes_aliases(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()

    db_session.delete(account)
    db_session.commit()
    assert db_session.query(Alias).count() == 0
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_models.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: 编写 models.py**

```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class YahooAccount(Base):
    __tablename__ = "yahoo_accounts"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    imap_password = Column(String, nullable=False)
    status = Column(String, default="normal")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    aliases = relationship("Alias", back_populates="account", cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "aliases"

    id = Column(Integer, primary_key=True)
    alias_email = Column(String, unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey("yahoo_accounts.id"), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    account = relationship("YahooAccount", back_populates="aliases")
```

- [ ] **Step 4: 编写 database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from models import Base

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """创建所有表。"""
    Base.metadata.create_all(engine)


def get_db():
    """FastAPI 依赖注入用的数据库会话生成器。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
uv run pytest tests/test_models.py -v
```

预期：5 passed

- [ ] **Step 6: 提交**

```bash
git add database.py models.py tests/conftest.py tests/test_models.py
git commit -m "feat: 数据库设置和 ORM 模型（Admin, YahooAccount, Alias）"
```

---

### Task 3: 管理员认证模块

**Files:**
- Create: `auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: 编写认证测试**

写入 `tests/test_auth.py`：

```python
from auth import hash_password, verify_password, create_session_cookie, verify_session_cookie


def test_hash_and_verify_password():
    hashed = hash_password("admin123")
    assert hashed != "admin123"
    assert verify_password("admin123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_session_cookie_roundtrip():
    cookie = create_session_cookie("admin")
    username = verify_session_cookie(cookie)
    assert username == "admin"


def test_session_cookie_invalid():
    result = verify_session_cookie("invalid_cookie_value")
    assert result is None
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_auth.py -v
```

预期：FAIL — `ImportError`

- [ ] **Step 3: 编写 auth.py**

```python
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

import config

_serializer = URLSafeTimedSerializer(config.SECRET_KEY)


def hash_password(password: str) -> str:
    """用 bcrypt 哈希密码。"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码与哈希是否匹配。"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_session_cookie(username: str) -> str:
    """创建签名的 session cookie。"""
    return _serializer.dumps(username, salt="session")


def verify_session_cookie(cookie: str, max_age: int = 86400) -> str | None:
    """验证 session cookie，返回 username 或 None。"""
    try:
        return _serializer.loads(cookie, salt="session", max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_auth.py -v
```

预期：3 passed

- [ ] **Step 5: 提交**

```bash
git add auth.py tests/test_auth.py
git commit -m "feat: 管理员认证模块（bcrypt 哈希 + itsdangerous session cookie）"
```

---

### Task 4: IMAP 邮件拉取客户端

**Files:**
- Create: `imap_client.py`
- Create: `tests/test_imap_client.py`

- [ ] **Step 1: 编写 IMAP 客户端测试（mock）**

写入 `tests/test_imap_client.py`：

```python
from unittest.mock import MagicMock, patch
from email.mime.text import MIMEText
from email.utils import formatdate

from imap_client import fetch_emails


def _make_raw_email(from_addr: str, to_addr: str, subject: str, body: str) -> bytes:
    msg = MIMEText(body)
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    return msg.as_bytes()


@patch("imap_client.imaplib.IMAP4_SSL")
def test_fetch_emails_returns_list(mock_imap_cls):
    mock_conn = MagicMock()
    mock_imap_cls.return_value = mock_conn
    mock_conn.login.return_value = ("OK", [])
    mock_conn.select.return_value = ("OK", [b"1"])

    raw = _make_raw_email("sender@test.com", "alias@yahoo.com", "验证码 123456", "你的验证码是 123456")
    mock_conn.search.return_value = ("OK", [b"1"])
    mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822)", raw)])

    emails = fetch_emails("main@yahoo.com", "app_password", "alias@yahoo.com", count=10)

    assert len(emails) == 1
    assert emails[0]["from"] == "sender@test.com"
    assert "123456" in emails[0]["subject"]
    mock_conn.logout.assert_called_once()


@patch("imap_client.imaplib.IMAP4_SSL")
def test_fetch_emails_empty_inbox(mock_imap_cls):
    mock_conn = MagicMock()
    mock_imap_cls.return_value = mock_conn
    mock_conn.login.return_value = ("OK", [])
    mock_conn.select.return_value = ("OK", [b"0"])
    mock_conn.search.return_value = ("OK", [b""])

    emails = fetch_emails("main@yahoo.com", "app_password", "alias@yahoo.com")

    assert emails == []
    mock_conn.logout.assert_called_once()


@patch("imap_client.imaplib.IMAP4_SSL")
def test_fetch_emails_connection_error(mock_imap_cls):
    mock_imap_cls.side_effect = OSError("连接失败")

    emails = fetch_emails("main@yahoo.com", "app_password", "alias@yahoo.com")

    assert emails is None
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_imap_client.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'imap_client'`

- [ ] **Step 3: 编写 imap_client.py**

```python
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

import config


def _decode_header_value(value: str) -> str:
    """解码 MIME 编码的邮件头部。"""
    if value is None:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_snippet(msg: email.message.Message, max_len: int = 200) -> str:
    """提取邮件正文前 max_len 个字符作为摘要。"""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")[:max_len]
        # 没有 text/plain，尝试 text/html
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                    # 简单去 HTML 标签
                    import re
                    text = re.sub(r"<[^>]+>", "", text)
                    return text.strip()[:max_len]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")[:max_len]
    return ""


def fetch_emails(
    account_email: str,
    imap_password: str,
    alias: str,
    count: int = 10,
) -> list[dict] | None:
    """
    连接雅虎 IMAP，搜索发往 alias 的邮件，返回最新 count 封。

    返回: [{"from": str, "subject": str, "date": str, "snippet": str}, ...]
    连接失败返回 None。
    """
    try:
        conn = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993, timeout=config.IMAP_TIMEOUT)
        conn.login(account_email, imap_password)
        conn.select("INBOX", readonly=True)

        _, data = conn.search(None, f'TO "{alias}"')
        msg_ids = data[0].split()
        if not msg_ids:
            conn.logout()
            return []

        # 取最新的 count 封
        msg_ids = msg_ids[-count:]
        msg_ids.reverse()

        emails = []
        for msg_id in msg_ids:
            _, msg_data = conn.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            _, from_addr = parseaddr(_decode_header_value(msg["From"]))
            subject = _decode_header_value(msg["Subject"])
            date_str = msg["Date"] or ""
            snippet = _extract_snippet(msg)

            emails.append({
                "from": from_addr,
                "subject": subject,
                "date": date_str,
                "snippet": snippet,
            })

        conn.logout()
        return emails

    except Exception:
        return None
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_imap_client.py -v
```

预期：3 passed

- [ ] **Step 5: 提交**

```bash
git add imap_client.py tests/test_imap_client.py
git commit -m "feat: IMAP 邮件拉取客户端（连接、搜索、MIME 解析）"
```

---

### Task 5: 管理后台路由

**Files:**
- Create: `routers/__init__.py`
- Create: `routers/admin.py`
- Create: `tests/test_admin.py`

- [ ] **Step 1: 编写管理后台路由测试**

写入 `routers/__init__.py`（空文件）。

写入 `tests/test_admin.py`：

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Admin, YahooAccount, Alias
from database import get_db
from auth import hash_password, create_session_cookie
from routers.admin import router as admin_router

app = FastAPI()
app.include_router(admin_router)


@pytest.fixture()
def client():
    engine = create_engine("sqlite:///:memory:")
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

    yield TestClient(app)
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


def test_add_alias(client):
    cookie = create_session_cookie("admin")
    # 先添加账号
    client.post(
        "/admin/accounts",
        data={"email": "test@yahoo.com", "imap_password": "secret"},
        cookies={"session": cookie},
    )
    # 添加别名
    resp = client.post(
        "/admin/aliases",
        data={"alias_email": "alias1@yahoo.com", "account_id": "1"},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303


def test_unauthenticated_access_redirects(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/admin/login" in resp.headers["location"]
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_admin.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'routers.admin'`

- [ ] **Step 3: 编写 routers/admin.py**

```python
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import hash_password, verify_password, create_session_cookie, verify_session_cookie
from database import get_db
from encryption import encrypt_password
from models import Admin, YahooAccount, Alias

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


def _get_current_admin(request: Request) -> str | None:
    """从 cookie 提取当前管理员用户名，未登录返回 None。"""
    cookie = request.cookies.get("session")
    if not cookie:
        return None
    return verify_session_cookie(cookie)


def _require_admin(request: Request):
    """依赖项：要求管理员登录，否则重定向。"""
    admin = _get_current_admin(request)
    if not admin:
        raise _redirect_to_login()
    return admin


class _redirect_to_login(Exception):
    pass


@router.exception_handler(_redirect_to_login)
async def redirect_to_login_handler(request: Request, exc: _redirect_to_login):
    return RedirectResponse("/admin/login", status_code=303)


# --- 登录/登出 ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin and verify_password(password, admin.password_hash):
        response = RedirectResponse("/admin/", status_code=303)
        response.set_cookie("session", create_session_cookie(username), httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "用户名或密码错误"})


@router.get("/logout")
async def logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("session")
    return response


# --- 管理后台主页 ---

@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    accounts = db.query(YahooAccount).all()
    aliases = db.query(Alias).all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "accounts": accounts,
        "aliases": aliases,
        "tab": "accounts",
    })


# --- 主账号 CRUD ---

@router.post("/accounts")
async def add_account(
    request: Request,
    email: str = Form(...),
    imap_password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    account = YahooAccount(email=email, imap_password=encrypt_password(imap_password))
    db.add(account)
    db.commit()
    return RedirectResponse("/admin/?tab=accounts", status_code=303)


@router.post("/accounts/{account_id}/delete")
async def delete_account(account_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    account = db.query(YahooAccount).get(account_id)
    if account:
        db.delete(account)
        db.commit()
    return RedirectResponse("/admin/?tab=accounts", status_code=303)


# --- 别名 CRUD ---

@router.post("/aliases")
async def add_alias(
    request: Request,
    alias_email: str = Form(...),
    account_id: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    alias = Alias(alias_email=alias_email, account_id=account_id)
    db.add(alias)
    db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)


@router.post("/aliases/{alias_id}/delete")
async def delete_alias(alias_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    alias = db.query(Alias).get(alias_id)
    if alias:
        db.delete(alias)
        db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)


@router.post("/aliases/{alias_id}/toggle")
async def toggle_alias(alias_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    alias = db.query(Alias).get(alias_id)
    if alias:
        alias.enabled = not alias.enabled
        db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_admin.py -v
```

预期：5 passed

- [ ] **Step 5: 提交**

```bash
git add routers/ tests/test_admin.py
git commit -m "feat: 管理后台路由（登录、主账号/别名 CRUD）"
```

---

### Task 6: 前台邮件拉取路由

**Files:**
- Create: `routers/mail.py`
- Create: `tests/test_mail.py`

- [ ] **Step 1: 编写邮件拉取路由测试**

写入 `tests/test_mail.py`：

```python
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, YahooAccount, Alias
from database import get_db
from encryption import encrypt_password
from routers.mail import router as mail_router

app = FastAPI()
app.include_router(mail_router)


@pytest.fixture()
def client():
    engine = create_engine("sqlite:///:memory:")
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_mail.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'routers.mail'`

- [ ] **Step 3: 编写 routers/mail.py**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from encryption import decrypt_password
from imap_client import fetch_emails
from models import Alias

router = APIRouter()


class FetchRequest(BaseModel):
    alias_email: str


@router.post("/api/mail/fetch")
async def fetch_mail(req: FetchRequest, db: Session = Depends(get_db)):
    # 查找别名
    alias = db.query(Alias).filter(
        Alias.alias_email == req.alias_email,
        Alias.enabled == True,
    ).first()

    if not alias:
        return {"success": False, "error": "未找到该邮箱", "emails": []}

    account = alias.account
    imap_password = decrypt_password(account.imap_password)

    emails = fetch_emails(account.email, imap_password, req.alias_email)

    if emails is None:
        return {"success": False, "error": "邮件服务暂时不可用，请稍后重试", "emails": []}

    return {"success": True, "error": None, "emails": emails}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_mail.py -v
```

预期：4 passed

- [ ] **Step 5: 提交**

```bash
git add routers/mail.py tests/test_mail.py
git commit -m "feat: 前台邮件拉取 API（查别名 → 解密凭证 → IMAP 拉取）"
```

---

### Task 7: HTML 模板

**Files:**
- Create: `templates/base.html`
- Create: `templates/index.html`
- Create: `templates/login.html`
- Create: `templates/admin.html`

- [ ] **Step 1: 编写 base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Yahoo 邮件查看{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #fafafa; }
        {% block extra_style %}{% endblock %}
    </style>
</head>
<body>
    {% block body %}{% endblock %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_script %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: 编写 index.html（前台极简风格）**

```html
{% extends "base.html" %}

{% block extra_style %}
body {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
}
.container { max-width: 500px; width: 100%; }
.mail-item {
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}
.mail-item:last-child { border-bottom: none; }
.mail-from { font-weight: 600; color: #333; font-size: 14px; }
.mail-subject { color: #555; font-size: 14px; }
.mail-meta { color: #999; font-size: 12px; }
.mail-snippet { color: #888; font-size: 13px; margin-top: 2px; }
#loading { display: none; }
#error-msg { display: none; }
#mail-list { display: none; }
#empty-msg { display: none; }
{% endblock %}

{% block body %}
<div class="container text-center">
    <h2 class="mb-4" style="font-weight: 300; color: #333;">📮 Yahoo 邮件查看</h2>
    <div class="mb-3">
        <input type="email" id="alias-input" class="form-control form-control-lg text-center"
               placeholder="输入别名邮箱地址..." style="border-radius: 8px;">
    </div>
    <button id="fetch-btn" class="btn btn-primary btn-lg w-100" style="border-radius: 8px;"
            onclick="fetchMails()">拉取邮件</button>

    <div id="loading" class="mt-4">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="mt-2 text-muted">正在拉取邮件...</p>
    </div>

    <div id="error-msg" class="alert alert-danger mt-4"></div>

    <div id="empty-msg" class="mt-4 text-muted">暂无邮件</div>

    <div id="mail-list" class="mt-4 text-start"></div>
</div>
{% endblock %}

{% block extra_script %}
<script>
async function fetchMails() {
    const alias = document.getElementById('alias-input').value.trim();
    if (!alias) return;

    document.getElementById('loading').style.display = 'block';
    document.getElementById('error-msg').style.display = 'none';
    document.getElementById('mail-list').style.display = 'none';
    document.getElementById('empty-msg').style.display = 'none';
    document.getElementById('fetch-btn').disabled = true;

    try {
        const resp = await fetch('/api/mail/fetch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({alias_email: alias})
        });
        const data = await resp.json();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('fetch-btn').disabled = false;

        if (!data.success) {
            document.getElementById('error-msg').textContent = data.error;
            document.getElementById('error-msg').style.display = 'block';
            return;
        }

        if (data.emails.length === 0) {
            document.getElementById('empty-msg').style.display = 'block';
            return;
        }

        const list = document.getElementById('mail-list');
        list.innerHTML = data.emails.map(e => `
            <div class="mail-item">
                <div class="d-flex justify-content-between">
                    <span class="mail-from">${escapeHtml(e.from)}</span>
                    <span class="mail-meta">${escapeHtml(e.date)}</span>
                </div>
                <div class="mail-subject">${escapeHtml(e.subject)}</div>
                <div class="mail-snippet">${escapeHtml(e.snippet)}</div>
            </div>
        `).join('');
        list.style.display = 'block';
    } catch (err) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('fetch-btn').disabled = false;
        document.getElementById('error-msg').textContent = '网络错误，请重试';
        document.getElementById('error-msg').style.display = 'block';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

document.getElementById('alias-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') fetchMails();
});
</script>
{% endblock %}
```

- [ ] **Step 3: 编写 login.html**

```html
{% extends "base.html" %}

{% block title %}管理员登录{% endblock %}

{% block extra_style %}
body {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
}
{% endblock %}

{% block body %}
<div style="max-width: 360px; width: 100%;">
    <h3 class="text-center mb-4">📮 管理员登录</h3>
    {% if error %}
    <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    <form method="post" action="/admin/login">
        <div class="mb-3">
            <input type="text" name="username" class="form-control" placeholder="用户名" required>
        </div>
        <div class="mb-3">
            <input type="password" name="password" class="form-control" placeholder="密码" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">登录</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 4: 编写 admin.html（顶部 Tab 导航）**

```html
{% extends "base.html" %}

{% block title %}管理后台{% endblock %}

{% block extra_style %}
body { background: #fff; }
{% endblock %}

{% block body %}
<div class="container-fluid">
    <nav class="navbar navbar-light bg-light border-bottom mb-3">
        <div class="container">
            <span class="navbar-brand">📮 管理后台</span>
            <a href="/admin/logout" class="btn btn-outline-danger btn-sm">退出登录</a>
        </div>
    </nav>

    <div class="container">
        <ul class="nav nav-tabs mb-3" id="adminTabs" role="tablist">
            <li class="nav-item">
                <a class="nav-link {% if tab == 'accounts' %}active{% endif %}"
                   href="/admin/?tab=accounts">主账号</a>
            </li>
            <li class="nav-item">
                <a class="nav-link {% if tab == 'aliases' %}active{% endif %}"
                   href="/admin/?tab=aliases">别名管理</a>
            </li>
        </ul>

        {% if tab == 'accounts' %}
        <!-- 主账号面板 -->
        <div class="d-flex justify-content-end mb-3">
            <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addAccountModal">+ 添加账号</button>
        </div>
        <table class="table table-hover">
            <thead>
                <tr><th>邮箱</th><th>别名数</th><th>状态</th><th>操作</th></tr>
            </thead>
            <tbody>
                {% for account in accounts %}
                <tr>
                    <td>{{ account.email }}</td>
                    <td>{{ account.aliases | length }}</td>
                    <td>
                        {% if account.status == 'normal' %}
                        <span class="badge bg-success">正常</span>
                        {% else %}
                        <span class="badge bg-danger">{{ account.status }}</span>
                        {% endif %}
                    </td>
                    <td>
                        <form method="post" action="/admin/accounts/{{ account.id }}/delete"
                              style="display:inline" onsubmit="return confirm('确定删除？关联的别名也会被删除。')">
                            <button class="btn btn-outline-danger btn-sm">删除</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
                {% if not accounts %}
                <tr><td colspan="4" class="text-center text-muted">暂无账号</td></tr>
                {% endif %}
            </tbody>
        </table>

        <!-- 添加账号 Modal -->
        <div class="modal fade" id="addAccountModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <form method="post" action="/admin/accounts">
                        <div class="modal-header">
                            <h5 class="modal-title">添加雅虎主账号</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">邮箱地址</label>
                                <input type="email" name="email" class="form-control" placeholder="user@yahoo.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">IMAP 应用密码</label>
                                <input type="password" name="imap_password" class="form-control" required>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="submit" class="btn btn-primary">添加</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        {% elif tab == 'aliases' %}
        <!-- 别名面板 -->
        <div class="d-flex justify-content-end mb-3">
            <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addAliasModal">+ 添加别名</button>
        </div>
        <table class="table table-hover">
            <thead>
                <tr><th>别名邮箱</th><th>所属主账号</th><th>状态</th><th>操作</th></tr>
            </thead>
            <tbody>
                {% for alias in aliases %}
                <tr>
                    <td>{{ alias.alias_email }}</td>
                    <td>{{ alias.account.email }}</td>
                    <td>
                        {% if alias.enabled %}
                        <span class="badge bg-success">启用</span>
                        {% else %}
                        <span class="badge bg-secondary">禁用</span>
                        {% endif %}
                    </td>
                    <td>
                        <form method="post" action="/admin/aliases/{{ alias.id }}/toggle" style="display:inline">
                            <button class="btn btn-outline-warning btn-sm">
                                {{ "禁用" if alias.enabled else "启用" }}
                            </button>
                        </form>
                        <form method="post" action="/admin/aliases/{{ alias.id }}/delete"
                              style="display:inline" onsubmit="return confirm('确定删除该别名？')">
                            <button class="btn btn-outline-danger btn-sm">删除</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
                {% if not aliases %}
                <tr><td colspan="4" class="text-center text-muted">暂无别名</td></tr>
                {% endif %}
            </tbody>
        </table>

        <!-- 添加别名 Modal -->
        <div class="modal fade" id="addAliasModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <form method="post" action="/admin/aliases">
                        <div class="modal-header">
                            <h5 class="modal-title">添加别名</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">别名邮箱</label>
                                <input type="email" name="alias_email" class="form-control" placeholder="alias@yahoo.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">所属主账号</label>
                                <select name="account_id" class="form-select" required>
                                    {% for account in accounts %}
                                    <option value="{{ account.id }}">{{ account.email }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="submit" class="btn btn-primary">添加</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: 提交**

```bash
git add templates/
git commit -m "feat: HTML 模板 — 前台极简风格 + 管理后台 Tab 导航"
```

---

### Task 8: 应用入口 + 初始管理员 + 冒烟测试

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 编写冒烟测试**

写入 `tests/test_main.py`：

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base
from database import get_db
from main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 初始化管理员（模拟 main.py 的 init_admin 逻辑）
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_main.py -v
```

预期：FAIL — `ImportError: cannot import name 'app' from 'main'`

- [ ] **Step 3: 编写 main.py**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import config
from auth import hash_password
from database import init_db, SessionLocal
from models import Admin
from routers.admin import router as admin_router
from routers.mail import router as mail_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建表 + 初始化管理员
    init_db()
    _ensure_admin()
    yield


def _ensure_admin():
    """确保默认管理员账号存在。"""
    db = SessionLocal()
    try:
        if not db.query(Admin).first():
            admin = Admin(
                username=config.ADMIN_USERNAME,
                password_hash=hash_password(config.ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.include_router(admin_router)
app.include_router(mail_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_main.py -v
```

预期：3 passed

- [ ] **Step 5: 运行全部测试**

```bash
uv run pytest -v
```

预期：全部通过（约 20 个测试）

- [ ] **Step 6: 手动冒烟测试**

```bash
cd /Users/jason/IdeaProjects/yahoo-email
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器验证：
1. 访问 `http://localhost:8000` — 看到前台极简页面
2. 访问 `http://localhost:8000/admin/login` — 用 admin/admin123 登录
3. 在后台添加一个主账号和别名
4. 回到前台输入别名地址，点击拉取

- [ ] **Step 7: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: 应用入口与冒烟测试 — 雅虎别名邮箱查看器完成"
```
