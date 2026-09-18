from datetime import datetime, timedelta
from typing import Any, Union, Optional
import jwt
import bcrypt
import logging
from .config import settings

logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu bằng thuật toán bcrypt an toàn cao."""
    pwd_bytes = password.encode("utf-8")[:72]  # bcrypt chuẩn giới hạn 72 bytes
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Xác thực mật khẩu người dùng.
    Hỗ trợ cả bcrypt hash và fallback plain-text (tự động tương thích trong quá trình migration).
    """
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        # Fallback migration cho mật khẩu cũ dạng plain text
        return plain_password == hashed_password
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return plain_password == hashed_password

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Tạo Access Token với thời gian hết hạn theo cấu hình."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Tạo Refresh Token với thời gian sống dài (mặc định 30 ngày)."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Giải mã và kiểm tra tính hợp lệ của Access Token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None

def decode_refresh_token(token: str) -> Optional[dict]:
    """Giải mã và kiểm tra tính hợp lệ của Refresh Token."""
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except Exception:
        return None
