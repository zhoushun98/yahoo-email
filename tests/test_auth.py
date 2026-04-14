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
