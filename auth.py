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
