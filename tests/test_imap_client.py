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
