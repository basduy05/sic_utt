import uuid
from fastapi import APIRouter, HTTPException, status
from ....core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)
from ....core.database import db_service
from ....models.pydantic.auth_schema import UserCreate, UserLogin, RefreshTokenRequest, TokenResponse

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate):
    """Đăng ký tài khoản người dùng mới với mật khẩu mã hóa bcrypt."""
    existing_user = await db_service.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = str(uuid.uuid4())
    hashed = get_password_hash(user_in.password)
    user_doc = {
        "id": user_id,
        "email": user_in.email,
        "password_hash": hashed,
        "full_name": user_in.full_name,
        "role": user_in.role
    }
    await db_service.create_user(user_doc)
    
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=user_in.email,
        full_name=user_in.full_name,
        role=user_in.role
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin):
    """Đăng nhập hệ thống, cấp Access Token & Refresh Token."""
    user = await db_service.get_user_by_email(user_in.email)
    if not user or not verify_password(user_in.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user["id"],
        email=user["email"],
        full_name=user.get("full_name", user["email"]),
        role=user.get("role", "user")
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(body: RefreshTokenRequest):
    """
    Cấp mới Access Token thông qua Refresh Token hợp lệ mà không cần đăng nhập lại.
    """
    payload = decode_refresh_token(body.refresh_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    user = await db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found"
        )
    
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user_id=user["id"],
        email=user["email"],
        full_name=user.get("full_name", user["email"]),
        role=user.get("role", "user")
    )
