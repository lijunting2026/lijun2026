from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "test123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_token_create_and_decode():
    data = {"sub": "user123", "role": "admin"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "admin"
