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


def _extract_body(msg: email.message.Message) -> tuple[str, str]:
    """
    提取邮件正文，返回 (plain_text, html)。
    优先提取 text/plain 和 text/html，均可能为空字符串。
    """
    import re
    plain = ""
    html = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if content_type == "text/plain" and not plain:
                plain = text
            elif content_type == "text/html" and not html:
                html = text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                html = text
            else:
                plain = text

    return plain, html


def _html_to_text(html: str) -> str:
    """简单地将 HTML 转换为纯文本。"""
    import re
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _make_snippet(plain: str, html: str, max_len: int = 200) -> str:
    """从正文生成摘要。"""
    if plain:
        return plain[:max_len]
    if html:
        return _html_to_text(html)[:max_len]
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
            plain, html = _extract_body(msg)
            snippet = _make_snippet(plain, html)
            # 完整正文：优先纯文本，否则从 HTML 转换
            body = plain if plain else _html_to_text(html)

            emails.append({
                "from": from_addr,
                "subject": subject,
                "date": date_str,
                "snippet": snippet,
                "body": body,
            })

        conn.logout()
        return emails

    except Exception:
        return None
