from cryptography.fernet import Fernet

import config

_fernet = Fernet(config.FERNET_KEY.encode())


def encrypt_password(plain: str) -> str:
    """加密 IMAP 密码，返回 base64 密文字符串。"""
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """解密 IMAP 密码，返回明文。"""
    return _fernet.decrypt(encrypted.encode()).decode()
