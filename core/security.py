from datetime import datetime, timedelta, timezone
from typing import Union, Any
from uuid import UUID
from jose import JWTError, jwt

import jwt
from passlib.context import CryptContext
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import AuthenticationFailedError, ErrorCode, ForbiddenError
from app.db.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    
async def verify_admin_from_access_token(
    payload: dict,
    session: AsyncSession
) -> User:
    user = await verify_user_from_access_token(
        payload=payload,
        session=session
    )
    if user.is_admin:
        return user
    else:
        raise ForbiddenError()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)