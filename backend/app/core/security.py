"""Authentication and authorization — JWT tokens + RBAC."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    token: str | None = Security(oauth2_scheme),
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate via JWT token or legacy API key. Returns RepUser or raises 401."""
    from app.models.schema import RepUser

    settings = get_settings()

    # Try JWT token first
    if token:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            sub = payload.get("sub")
            if sub is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            user = await db.get(RepUser, int(sub))
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    # Fallback: API key check
    if api_key and getattr(settings, "api_key", None):
        if api_key == settings.api_key:
            result = await db.execute(select(RepUser).limit(1))
            user = result.scalar_one_or_none()
            if user:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles):
    """Dependency factory: restrict endpoint to specific roles."""
    async def role_checker(current_user=Depends(get_current_user)):
        from app.models.schema import UserRole
        if current_user.role not in [UserRole(r) if isinstance(r, str) else r for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(str(r) for r in roles)}",
            )
        return current_user
    return role_checker
