"""Authentication utilities: hashing passwords, creating JWT, verifying tokens."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.client import Client

# Bcrypt password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token extractor (reads Authorization: Bearer <token>)

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Return hashed version of password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Check if entered password matches stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Create JWT token containing `sub` (client_id)."""
    to_encode = data.copy()

    time_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + time_delta
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Decode token and return payload or raise HTTP 401."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload

    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from err


async def get_current_client(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> Client:
    """Return currently authenticated client from DB."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated - missing Authorization header",
        )

    token = credentials.credentials
    payload = decode_token(token)
    client_id = payload.get("sub")

    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.is_disabled:
        raise HTTPException(status_code=403, detail="Account disabled")

    return client
