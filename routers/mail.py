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
