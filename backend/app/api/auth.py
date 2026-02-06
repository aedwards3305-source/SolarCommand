"""Auth endpoints — login, me, register."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.schema import RepUser, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str
    role: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    phone: str | None
    role: str
    is_active: bool


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    phone: str | None = None
    role: str = "rep"


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    result = await db.execute(select(RepUser).where(RepUser.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # If user has no password hash yet (legacy seed data), set it on first login
    if not user.password_hash:
        user.password_hash = hash_password(payload.password)
        await db.flush()
    elif not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: RepUser = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user (admin-only in production, open for MVP)."""
    existing = await db.execute(select(RepUser).where(RepUser.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        role = UserRole(payload.role)
    except ValueError:
        role = UserRole.rep

    user = RepUser(
        email=payload.email,
        name=payload.name,
        phone=payload.phone,
        role=role,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        is_active=user.is_active,
    )
