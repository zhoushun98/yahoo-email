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
