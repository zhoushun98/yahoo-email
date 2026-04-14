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


# --- 登录/登出 ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin and verify_password(password, admin.password_hash):
        response = RedirectResponse("/admin/", status_code=303)
        response.set_cookie("session", create_session_cookie(username), httponly=True)
        return response
    return templates.TemplateResponse(request, "login.html", {"error": "用户名或密码错误"})


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
    tab = request.query_params.get("tab", "accounts")
    accounts = db.query(YahooAccount).all()
    aliases = db.query(Alias).all()
    return templates.TemplateResponse(request, "admin.html", {
        "accounts": accounts,
        "aliases": aliases,
        "tab": tab,
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
    account = db.get(YahooAccount, account_id)
    if account:
        db.delete(account)
        db.commit()
    return RedirectResponse("/admin/?tab=accounts", status_code=303)


# --- 别名 CRUD ---

@router.post("/aliases")
async def add_alias(
    request: Request,
    alias_emails: str = Form(...),
    account_id: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    # 支持批量添加，一行一个邮箱
    for line in alias_emails.splitlines():
        email = line.strip()
        if not email:
            continue
        # 跳过已存在的别名
        exists = db.query(Alias).filter(Alias.alias_email == email).first()
        if not exists:
            db.add(Alias(alias_email=email, account_id=account_id))
    db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)


@router.post("/aliases/{alias_id}/delete")
async def delete_alias(alias_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    alias = db.get(Alias, alias_id)
    if alias:
        db.delete(alias)
        db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)


@router.post("/aliases/{alias_id}/toggle")
async def toggle_alias(alias_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _get_current_admin(request)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    alias = db.get(Alias, alias_id)
    if alias:
        alias.enabled = not alias.enabled
        db.commit()
    return RedirectResponse("/admin/?tab=aliases", status_code=303)
