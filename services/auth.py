from fastapi import Depends, Header, Request
from google.auth.transport import requests
from jwt import InvalidSignatureError
from app.core.logging import logger
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from google.oauth2 import id_token
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.security import decode_jwt, verify_admin_from_access_token, verify_jwt_version, verify_user_from_access_token
from app.core.exceptions import AuthenticationFailedError, ForbiddenError, ErrorCode
from app.db.models import User
from app.db.session import get_session
from app.core.config import settings


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ANDROID_GOOGLE_CLIENT_ID = settings.ANDROID_GOOGLE_CLIENT_ID
IOS_GOOGLE_CLIENT_ID = settings.IOS_GOOGLE_CLIENT_ID


async def get_user_from_passwordless_login_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    
    try:
        payload = decode_jwt(token)
        if not payload:
            raise AuthenticationFailedError(
                message="Invalid or expired token", 
                error_code=ErrorCode.INVALID_TOKEN.value
            )
        
        email = payload.get("sub")
        if not email:
            raise AuthenticationFailedError(
                message="Invalid token payload", 
                error_code=ErrorCode.INVALID_TOKEN.value
            )
        
        user = await session.exec(
            select(User).where(
                User.email == email
            )
        )   
        user_res = user.first()     
        if not user_res:
            raise AuthenticationFailedError(
                message="User not found"
            )
            
        return user_res
    
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)    
        raise
    
    except InvalidSignatureError as e:
        logger.error("Invalid JWT: {}", str(e), exc_info=True)
        raise AuthenticationFailedError(
            message="User not found"
        )
    
    except Exception as e:
        logger.error("Unexpected error: {}", str(e), exc_info=True)
        raise


async def get_user_from_access_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency to get the current user from the JWT token. Used for all routes except admin routes.

    Args:
        token (str, optional): JWT token. Defaults to Depends(oauth2_scheme).
        session (AsyncSession, optional): Database session. Defaults to Depends(get_session).

    Raises:
        AuthenticationFailedError: If the token is invalid or expired, or if the user is not found.
        InvalidSignatureError: If the token signature is invalid.
        Exception: If any other error occurs.

    Returns:
        User: The user object corresponding to the token.
    """
    
    try:
        payload = decode_jwt(token)
        if not payload:
            raise AuthenticationFailedError(
                message="Invalid or expired token", 
                error_code=ErrorCode.INVALID_TOKEN.value
            )
            
        user = await verify_user_from_access_token(
            payload=payload,
            session=session
        )
            
        verify_jwt_version(
            payload=payload,
            user=user
        )
            
        return user
    
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)    
        raise
    
    except InvalidSignatureError as e:
        logger.error("Invalid JWT: {}", str(e), exc_info=True)
        raise AuthenticationFailedError(
            message="User not found"
        )
    
    except Exception as e:
        logger.error("Unexpected error: {}", str(e), exc_info=True)
        raise
    
    
async def get_admin_from_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency to get the current admin from the JWT token. Used for admin routes.
    This function is similar to get_user_from_access_token, but it also checks if the user is an admin.

    Args:
        token (str, optional): JWT token. Defaults to Depends(oauth2_scheme).
        session (AsyncSession, optional): Database session. Defaults to Depends(get_session).

    Raises:
        AuthenticationFailedError: If the token is invalid or expired, or if the user is not found.
        InvalidSignatureError: If the token signature is invalid.
        Exception: If any other error occurs.
        
    Returns:
        User: The user object corresponding to the token.
    """
    
    try:
        payload = decode_jwt(token)
        if not payload:
            raise AuthenticationFailedError(
                message="Invalid or expired token", 
                error_code=ErrorCode.INVALID_TOKEN.value
            )
        
        admin = await verify_admin_from_access_token(
            payload=payload,
            session=session
        )
        
        verify_jwt_version(
            payload=payload,
            user=admin
        )
        
        return admin
    
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)    
        raise
    
    except ForbiddenError as e:
        logger.error("User is not an admin: {}", str(e), exc_info=True)    
        raise
    
    except InvalidSignatureError as e:
        logger.error("Invalid JWT: {}", str(e), exc_info=True)
        raise AuthenticationFailedError(message="User not found")
    
    except Exception as e:
        logger.error("Unexpected error: {}", str(e), exc_info=True)
        raise
    
    
def verify_google_token(
    id_token_str: str
):
    request_obj = requests.Request()
    for audience in (ANDROID_GOOGLE_CLIENT_ID, IOS_GOOGLE_CLIENT_ID):
        try:
            return id_token.verify_oauth2_token(
                id_token=id_token_str, 
                request=request_obj, 
                audience=audience
            )
        except Exception:
            continue
    AuthenticationFailedError(message="Invalid Google Token")


async def verify_video_processor_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationFailedError(message="Missing or invalid token")

    token = authorization.removeprefix("Bearer ").strip()

    if token != settings.VIDEO_PROCESSOR_TOKEN:
        raise ForbiddenError()
    
    
async def verify_ebook_processor_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationFailedError(message="Missing or invalid token")

    token = authorization.removeprefix("Bearer ").strip()

    if token != settings.EBOOK_PROCESSOR_TOKEN:
        raise ForbiddenError()


async def admin_or_video_processor(
    authorization: str = Header(None),
    request: Request = None,
    session: "AsyncSession" = Depends(get_session),
):
    try:
        await verify_video_processor_token(authorization)
        return None  
    except Exception:
        pass

    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
        if not token and request:
            token = request.cookies.get("access_token")
        if not token:
            raise AuthenticationFailedError(message="No token found")
        user = await get_admin_from_token(token=token, session=session)
        return user  
    except Exception:
        pass

    raise ForbiddenError()


async def admin_or_ebook_processor(
    authorization: str = Header(None),
    request: Request = None,
    session: "AsyncSession" = Depends(get_session),
):
    try:
        await verify_ebook_processor_token(authorization)
        return None  
    except Exception:
        pass

    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
        if not token and request:
            token = request.cookies.get("access_token")
        if not token:
            raise AuthenticationFailedError(message="No token found")
        user = await get_admin_from_token(token=token, session=session)
        return user  
    except Exception:
        pass

    raise ForbiddenError()