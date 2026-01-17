from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.schemas.avatar import AvatarResponse, AvatarsCreate
from app.db.session import get_session
from app.db.models import Avatar, User
from app.core.logging import logger
from app.schemas.response import SuccessResponse
from app.services.auth import get_user_from_access_token, get_admin_from_token

from app.utils.gcs import delete_blob_from_gcs


router = APIRouter(prefix="/avatars", tags=["Avatars"])


@router.post("")
async def create(
    avatars: AvatarsCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> List[AvatarResponse]:
    
    try:            
        avatar_urls = avatars.urls  
        uploaded_avatars = [] 
        
        for url in avatar_urls:
            
            new_avatar = Avatar(url=url)  
            session.add(new_avatar)
            await session.flush()
            
            uploaded_avatars.append(
                AvatarResponse(
                    id=new_avatar.id,
                    url=new_avatar.url
                )
            )
            
        await session.commit()
        return uploaded_avatars  
        
    except Exception as e:
        logger.error("Error creating avatars: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.get("")
async def get_avatars(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> List[AvatarResponse]:
    
    """Get avatars

    Args:
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).
        user (User, optional): User authentication required. Defaults to Depends(get_user_from_access_token).

    Raises:
        InternalServerError: Unexpected error occurs.

    Returns:
        List[AvatarResponse]: List of avatars.
    """
    try:    
        result = await session.exec(
            select(Avatar)
        )
        avatars = result.all()

        return [
            AvatarResponse(
                id=avatar.id,
                url=avatar.url,
            )
            for avatar in avatars
        ]
    
    except Exception as e:
        logger.error("Error getting avatars: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.delete("/{avatar_id}")
async def delete_avatar(
    avatar_id: UUID, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> SuccessResponse:
    
    """Delete an avatar by ID. Also deletes the avatar from GCS.

    Args:
        avatar_id (UUID): ID of avatar to be deleted.
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).
        user (User, optional): User authentication required. Defaults to Depends(get_user_from_access_token).

    Raises:
        ResourceNotFoundError: Avatar with avatar_id not found
        InternalServerError: An unexpected error occurs.

    Returns:
        SuccessResponse: Contains a message saying "Avatar deleted."
    """
    try:                
        avatar = await session.get(Avatar, avatar_id)
        if not avatar:
            raise ResourceNotFoundError(message="Avatar not found")
        
        delete_blob_from_gcs(avatar.url)
        
        await session.delete(avatar)
        await session.commit()

        return SuccessResponse(
            message="Avatar deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("Avatar not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error deleting avatar: {}", str(e), exc_info=True)
        raise InternalServerError()