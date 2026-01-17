from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import InternalServerError, ValidationError
from app.db.session import get_session
from app.db.models import User
from app.core.logging import logger
from app.schemas.file_upload import AdventureURLGet, ThemeIconURLGet, ThumbnailURLGet, QuizURLGet, AvatarURLGet
from app.services.auth import get_admin_from_token
from app.utils.gcs import get_quiz_signed_url, get_theme_icon_signed_url, get_video_signed_url, get_thumbnail_signed_url, get_avatar_signed_url, get_ebook_signed_url


router = APIRouter(prefix="/gcs-urls", tags=["File Upload"])
    
    
@router.post("/video")
async def get_video_urls(
    file_upload_data: AdventureURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        video_filename = file_upload_data.filename
        thumbnail = file_upload_data.thumbnail
                
        video_urls = get_video_signed_url(video_filename)
        video_upload_url = video_urls['upload_url']
        video_public_url = video_urls['public_url']
        
        thumbnail_urls = get_thumbnail_signed_url(thumbnail)
        thumbnail_upload_url = thumbnail_urls['upload_url']
        thumbnail_public_url = thumbnail_urls['public_url']
        
        return {
            "video_upload_url": video_upload_url,
            "thumbnail_upload_url": thumbnail_upload_url,
            "video_public_url": video_public_url,
            "thumbnail_public_url": thumbnail_public_url
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting video URLs: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/ebook")
async def get_ebook_urls(
    file_upload_data: AdventureURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        ebook_filename = file_upload_data.filename
        thumbnail = file_upload_data.thumbnail
                
        ebook_urls = get_ebook_signed_url(ebook_filename)
        ebook_upload_url = ebook_urls['upload_url']
        ebook_public_url = ebook_urls['public_url']
        
        if thumbnail:
            thumbnail_urls = get_thumbnail_signed_url(thumbnail)
            thumbnail_upload_url = thumbnail_urls['upload_url']
            thumbnail_public_url = thumbnail_urls['public_url']
            
        else:
            thumbnail_upload_url = None
            thumbnail_public_url = None
        
        return {
            "ebook_upload_url": ebook_upload_url,
            "thumbnail_upload_url": thumbnail_upload_url,
            "ebook_public_url": ebook_public_url,
            "thumbnail_public_url": thumbnail_public_url
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting eBook URLs: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/thumbnail")
async def get_thumbnail_urls(
    file_upload_data: ThumbnailURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        thumbnail = file_upload_data.thumbnail
        
        thumbnail_urls = get_thumbnail_signed_url(thumbnail)
        thumbnail_upload_url = thumbnail_urls['upload_url']
        thumbnail_public_url = thumbnail_urls['public_url']
        
        return {
            "thumbnail_upload_url": thumbnail_upload_url,
            "thumbnail_public_url": thumbnail_public_url
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting thumbnail URLs: {}", str(e), exc_info=True)
        raise InternalServerError()

    
@router.post("/avatar")
async def get_avatar_urls(
    file_upload_data: AvatarURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        avatar_filename = file_upload_data.filename
                
        avatar_urls = get_avatar_signed_url(avatar_filename)
        avatar_upload_url = avatar_urls['upload_url']
        avatar_public_url = avatar_urls['public_url']
        
        return {
            "avatar_upload_url": avatar_upload_url,
            "avatar_public_url": avatar_public_url,
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting avatar URLs: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/theme-icon")
async def get_theme_icon_urls(
    file_upload_data: ThemeIconURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        theme_icon_name = file_upload_data.icon_name
                
        icon_urls = get_theme_icon_signed_url(theme_icon_name)
        icon_upload_url = icon_urls['upload_url']
        icon_public_url = icon_urls['public_url']
        
        return {
            "icon_upload_url": icon_upload_url,
            "icon_public_url": icon_public_url,
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting theme icon URLs: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/quiz")
async def get_quiz_urls(
    file_upload_data: QuizURLGet,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
):
    
    try:
        quiz_filename = file_upload_data.filename
                
        quiz_urls = get_quiz_signed_url(quiz_filename)
        quiz_upload_url = quiz_urls['upload_url']
        quiz_public_url = quiz_urls['public_url']
        
        return {
            "quiz_upload_url": quiz_upload_url,
            "quiz_public_url": quiz_public_url,
        }  
        
    except ValidationError as e:
        logger.error("Invalid extension: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error getting quiz URLs: {}", str(e), exc_info=True)
        raise InternalServerError()