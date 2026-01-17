from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from sqlalchemy.orm import joinedload
from app.db.session import get_session
from app.db.models import Avatar, User, UserProfile
from app.core.logging import logger
from app.schemas.response import SuccessResponse
from app.services.auth import get_admin_from_token, get_user_from_access_token
from app.utils.profile import search_profile


router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("")
async def create(
    profile_data: ProfileCreate, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> ProfileResponse:
    
    try:          
        new_profile = UserProfile(
            first_name=profile_data.first_name, 
            last_name=profile_data.last_name,
            date_of_birth=profile_data.date_of_birth,
            avatar_id=profile_data.avatar_id,
            user_id=user.id,
            classroom_id=profile_data.classroom_id if profile_data.classroom_id else None
        )
                
        session.add(new_profile)
        await session.commit()
                
        return ProfileResponse(
            id=new_profile.id,
            first_name=new_profile.first_name,
            last_name=new_profile.last_name,
            date_of_birth=new_profile.date_of_birth,
        ) 
                
    except Exception as e:
        logger.error("Error creating profile: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.get("/all")
async def get_all_profiles(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token),
    q: Optional[str] = Query(None),
    offset: int = Query(0),
    limit: int = Query(10)
) -> List[ProfileResponse]:
    
    try:
        
        query = (
            select(UserProfile)
            .options(joinedload(UserProfile.avatar), joinedload(UserProfile.classroom))
            .offset(offset)
            .limit(limit)
        )
        
        if q:
            query = search_profile(query, q)
        
        # Fetch profiles and join with avatars
        result = await session.exec(query)
        profiles = result.all()

        return [
            ProfileResponse(
                id=profile.id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                date_of_birth=profile.date_of_birth,
                avatar_url=profile.avatar.url if profile.avatar else None,
                classroom_name=profile.classroom.name if profile.classroom else None
            )
            for profile in profiles
        ]
    
    except Exception as e:
        logger.error("Error getting user's profiles: {}", str(e), exc_info=True)
        raise InternalServerError()

    
@router.patch("/{profile_id}")
async def update(
    profile_id: UUID, 
    profile_data: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> ProfileResponse:
    
    try:       
        result = await session.exec(
            select(UserProfile)
            .options(joinedload(UserProfile.avatar))
            .where(UserProfile.id == profile_id)
        )
        profile = result.first()
        
        # Ensure profile belongs to user making the request.
        if not profile or profile.user_id != user.id:
            raise ResourceNotFoundError(message="Profile not found")
        
        # If avatar_id is being updated, fetch the new avatar
        if profile_data.avatar_id:
            avatar = await session.get(Avatar, profile_data.avatar_id)
            if not avatar:
                raise ResourceNotFoundError(message="Avatar not found")
            
            profile.avatar_id = avatar.id  
        
        # Update the profile fields
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        
        await session.commit()
        await session.refresh(profile)
                
        return ProfileResponse(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            date_of_birth=profile.date_of_birth,
            avatar_url=profile.avatar.url if profile.avatar else None
        )
     
    except ResourceNotFoundError as e:
        logger.error("Profile not found: {}", str(e), exc_info=True)
        raise    
                
    except Exception as e:
        logger.error("Error updating profile: {}", str(e), exc_info=True)
        raise InternalServerError()
    

@router.get("/{profile_id}")
async def get_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> ProfileResponse:    
    
    try:
        result = await session.exec(
            select(UserProfile)
            .options(joinedload(UserProfile.avatar), joinedload(UserProfile.classroom))
            .where(UserProfile.id == profile_id)
        )
        profile = result.first()
        
        if not profile:
            raise ResourceNotFoundError(message="Profile not found")
        
        return ProfileResponse(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            date_of_birth=profile.date_of_birth,
            avatar_url=profile.avatar.url if profile.avatar else None,
            classroom_name=profile.classroom.name if profile.classroom else None
        )
    
    except ResourceNotFoundError as e:
        logger.error("Profile not found: {}", str(e), exc_info=True)
        raise    
                
    except Exception as e:
        logger.error("Error getting profile: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.get("")
async def get_user_profiles(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> List[ProfileResponse]:
    
    try:
        
        result = await session.exec(
            select(UserProfile)
            .options(joinedload(UserProfile.avatar))
            .where(UserProfile.user_id == user.id, UserProfile.classroom_id.is_(None))
        )
        
        profiles = result.all()

        return [
            ProfileResponse(
                id=profile.id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                date_of_birth=profile.date_of_birth,
                avatar_url=profile.avatar.url if profile.avatar else None
            )
            for profile in profiles
        ]
    
    except Exception as e:
        logger.error("Error getting user's profiles: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: UUID, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> SuccessResponse:
    
    try:
        result = await session.exec(
            select(UserProfile).where(
                UserProfile.id == profile_id,
                UserProfile.user_id == user.id  
            )
        )
        profile = result.first()

        if not profile:
            raise ResourceNotFoundError(message="Profile not found")

        await session.delete(profile)
        await session.commit()

        return SuccessResponse(
            message="Profile deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("Profile not found: {}", str(e), exc_info=True)
        raise
    

    except Exception as e:
        logger.error("Error deleting profile: {}", str(e), exc_info=True)
        raise InternalServerError()