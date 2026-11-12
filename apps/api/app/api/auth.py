"""Authentication endpoints: register, login, me, change-password."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.models import User, AuditLog

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    subscription_tier: str
    telegram_user_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


def _user_public(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "subscription_tier": user.subscription_tier,
        "telegram_user_id": user.telegram_user_id,
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account and return a token."""
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        name=req.name,
        subscription_tier="free",
    )
    db.add(user)
    await db.flush()

    db.add(AuditLog(user_id=user.id, action="register", entity_type="user", entity_id=user.id))
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id), {"email": user.email, "tier": user.subscription_tier})
    return TokenResponse(access_token=token, user=_user_public(user))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return a token."""
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalars().first()

    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    db.add(AuditLog(user_id=user.id, action="login", entity_type="user", entity_id=user.id))
    await db.commit()

    token = create_access_token(str(user.id), {"email": user.email, "tier": user.subscription_tier})
    return TokenResponse(access_token=token, user=_user_public(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return the current authenticated user."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        subscription_tier=user.subscription_tier,
        telegram_user_id=user.telegram_user_id,
        created_at=user.created_at,
    )


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")

    user.password_hash = hash_password(req.new_password)
    db.add(AuditLog(user_id=user.id, action="change_password", entity_type="user", entity_id=user.id))
    await db.commit()
    return {"status": "ok", "message": "Password changed"}


class TelegramLinkRequest(BaseModel):
    telegram_user_id: str


@router.post("/link-telegram")
async def link_telegram(
    req: TelegramLinkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a Telegram chat id to the account for alerts."""
    user.telegram_user_id = req.telegram_user_id
    db.add(AuditLog(user_id=user.id, action="link_telegram", entity_type="user", entity_id=user.id))
    await db.commit()
    return {"status": "ok", "telegram_user_id": req.telegram_user_id}
