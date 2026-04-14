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
    return templates.TemplateResponse(request, "index.html", {})
