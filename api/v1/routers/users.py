from fastapi import APIRouter, Depends, Query
from typing import List
from sqlmodel import select, delete, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import InternalServerError, ResourceNotFoundError, ValidationError
from app.schemas.response import SuccessResponse
from app.schemas.user import UserResponse, UserUpdate
from app.db.session import get_session
from app.db.models import Classroom, User, UserProfile, UserSSO
from app.core.logging import logger
from app.services.auth import get_admin_from_token, get_user_from_access_token
from app.utils.user import validate_email_uniqueness


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def get_users(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token),
    offset: int = Query(0),
    limit: int = Query(10),
    is_admin: bool = Query(None)
) -> List[UserResponse]:
    try:
        query = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)

        result = await session.exec(query)
        users = result.all()

        return [
            UserResponse(
                id=user.id,
                email=user.email,
                created_at=str(user.created_at),
                email_verified_at=str(user.email_verified_at) if user.email_verified_at else None,
                is_admin=user.is_admin
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error("Error getting users: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.delete("/family_account")
async def delete_family_account(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> SuccessResponse:
    try:
        if user.is_family_account is False:
            raise ValidationError(message="You don't have a family account")
        
        user.is_family_account = False
        session.add(user)
        
        await session.exec(
            delete(UserProfile)
            .where(and_(
                UserProfile.user_id==user.id,
                UserProfile.classroom_id.is_(None)
            ))
        )
        await session.commit()
        return SuccessResponse(
            message="Family account deleted",
            data=None
        )
        
    except ValidationError as e:
        logger.error("User attempting to delete their family account even though they don't have one: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error deleting family account: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.delete("/teacher_account")
async def delete_teacher_account(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> SuccessResponse:
    try:
        if user.is_teacher_account is False:
            raise ValidationError(message="You don't have a teacher account")
        
        user.is_teacher_account = False
        session.add(user)
        
        await session.exec(
            delete(Classroom)
            .where(Classroom.user_id==user.id)
        )
        await session.commit()
        return SuccessResponse(
            message="Teacher account deleted",
            data=None
        )
        
    except ValidationError as e:
        logger.error("User attempting to delete their family account even though they don't have one: {}", str(e), exc_info=True)
        raise
    except Exception as e:
        logger.error("Error deleting teacher account: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.delete("")
async def delete_user(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> SuccessResponse:
    
    """Delete a user instance from the db.

    Args:
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).
        user (User, optional): The authenticated user. Request requires authentication.  Defaults to Depends(get_user_from_access_token).

    Raises:
        ResourceNotFoundError: Raised if email extracted from token does not belong to a user.
        InternalServerError: For unexpected errors.

    Returns:
        SuccessResponse: Contains a "User deleted" message
    """
    try:
        await session.delete(user)
        await session.commit()

        return SuccessResponse(
            message="User deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("User not found: {}", str(e), exc_info=True)
        raise

    except Exception as e:
        logger.error("Error deleting user: {}", str(e), exc_info=True)
        raise InternalServerError()
        
        
@router.patch('')
async def update(
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> UserResponse:
    
    try:    
        if user_data.email:
            await validate_email_uniqueness(user_data.email, session)
            user.email_verified_at = None
            user.jwt_version = user.jwt_version + 1
            
            # delete associated sso
            await session.exec(
                delete(UserSSO).where(
                    UserSSO.user_id == user.id
                )
            )

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        session.add(user)
        await session.commit()

        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=str(user.created_at),
            email_verified_at=str(user.email_verified_at) if user.email_verified_at else None,
            school=user.school,
            is_family_account=user.is_family_account,
            is_teacher_account=user.is_teacher_account,
            first_name=user.first_name,
            last_name=user.last_name
        )
                
    except ValidationError as e:
        logger.error("Validation error: {}", str(e), exc_info=True)    
        raise
    
    except Exception as e:
        logger.error("Error updating user: {}", str(e), exc_info=True)
        raise InternalServerError()