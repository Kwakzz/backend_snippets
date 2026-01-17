from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.db.session import get_session
from app.db.models import Adventure, User, Video, VideoVariant
from app.core.logging import logger
from app.schemas.response import SuccessResponse
from app.schemas.video import VideoResponse, VideoStoreMetadata, VideoUpdate, VideoCreate, VideosResponse
from app.services.auth import admin_or_video_processor, get_user_from_access_token, get_admin_from_token, verify_video_processor_token
from app.utils.adventure import create_adventure, delete_adventure
from app.utils.video import get_new_videos

from app.utils.s3 import delete_s3_folder_contents
from app.utils.gcs import delete_blob_from_gcs
from app.utils.notifications import notify_all_users
from app.core.rate_limiter import get_rate_limiter
from app.core.config import settings
from app.services.email import send_email
from app.utils.cloud_job_init import execute_video_processing_job


router = APIRouter(prefix="/videos", tags=["Videos"])
limiter = get_rate_limiter()


FULL_VIDEO_TYPE = "full"
CHUNKED_VIDEO_TYPE = "chunked"
    
        
@router.post("")
@limiter.limit("3/minute")
async def upload_video(
    request: Request,
    video_data: VideoCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> VideoResponse:  
    
    try:
        new_adventure = await create_adventure(
            session=session, 
            thumbnail_url=video_data.thumbnail_url,
            series_id=video_data.series_id,
            title=video_data.title
        )
        
        video = Video(adventure_id=new_adventure.id)
        session.add(video)
        await session.commit()
        await session.refresh(video)
        await session.refresh(new_adventure, ["series"])
        
        execution_id = await execute_video_processing_job(
            video_id=str(video.id),
            video_url=str(video_data.video_url)
        )
        logger.info(f"Started video processing job with execution ID: {execution_id}")
        
        return VideoResponse(
            id=video.id,
            type=video.video_type,
            adventure_id=new_adventure.id,
            series= new_adventure.series.name,
            title=new_adventure.title,
            message="Video processing started"
        )
    
    except Exception as e:
        await session.rollback()
        logger.error("Error creating video: {}", str(e), exc_info=True)
        delete_blob_from_gcs(video_data.thumbnail_url)
        delete_blob_from_gcs(video_data.video_url)
        raise InternalServerError() 
    

@router.post("/store-metadata")
async def store_metadata(
    metadata: VideoStoreMetadata,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_video_processor_token)
) -> VideoResponse:  
    
    try:
        video = await session.get(
            Video,
            metadata.video_id,
            options=[selectinload(Video.adventure)]
        )
        if not video:
            raise ResourceNotFoundError(message="Video not found")
            
        video.hls_url = metadata.hls_url
        video.duration = metadata.duration
        # video.subtitle_url = metadata.subtitle_url

        for variant in metadata.variants:
            resolution, bitrate, url = variant
            variant_entry = VideoVariant(
                video_id=video.id,
                resolution=resolution,
                bitrate=bitrate,
                url=url
            )
            session.add(variant_entry)
            
        await session.commit()
        
        # Notify users about new video content
        title = "New Video Available!"
        body = f"A new video titled '{video.adventure.title}' is now available to watch."
        await notify_all_users(title, body)
        
        # Notify admin about new video content
        send_email(
            to_email="wonderspacedapp@gmail.com",
            subject="New Video Available!",
            body_html=f"<p>Hi Edna,</p><p>The upload of the video titled '{video.adventure.title}' was successful. Users can now watch it on the Wonderspaced app.</p><p>Thanks for uploading.</p>"
        )
        
        logger.info(f"Metadata stored for video {metadata.video_id}")
        
        return VideoResponse(
            id=video.id,
            adventure_id=video.adventure_id,
            type=video.video_type,
            title=video.adventure.title,
            thumbnail=video.adventure.thumbnail,
            hls_url=video.hls_url,
            duration=video.duration,
            # subtitle_url=video.subtitle_url
        )
        
    except ResourceNotFoundError as e:
        logger.error("Video not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error storing video metadata: {}", str(e), exc_info=True)
        raise InternalServerError()
    

@router.get("")
async def get_videos(
    q: str = None,
    theme_param: str = None,
    series_param: str = None,
    videos_offset: int = Query(0),
    videos_limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:

        videos = await get_new_videos(
            session=session,
            offset=videos_offset,
            limit=videos_limit,
            min_similarity=min_similarity,
            q=q,
            series_param=series_param,
            theme_param=theme_param
        )

        return VideosResponse(videos=videos)

    except Exception as e:
        logger.error("Error getting videos: {}", str(e), exc_info=True)
        raise InternalServerError()

    
@router.delete("/{video_id}")
async def delete_video(
    video_id: UUID, 
    session: AsyncSession = Depends(get_session),
    _: User = Depends(admin_or_video_processor),
):
    """
    Deletes a video and its associated resources.
    This endpoint deletes a video specified by its UUID. It also removes related HLS files from S3 storage and subtitle files from Google Cloud Storage if they exist. The associated adventure is deleted, which cascades to delete the video record. Only users with admin or video processor roles are authorized to perform this action.
    Args:
        video_id (UUID): The unique identifier of the video to delete.
        session (AsyncSession, optional): The database session dependency.
        _ (User, optional): The authenticated user, must have admin or video processor privileges.
    Raises:
        ResourceNotFoundError: If the video with the given ID does not exist.
        InternalServerError: If an unexpected error occurs during deletion.
    Returns:
        SuccessResponse: A response indicating successful deletion of the video.
    """
    try:
        
        video = await session.get(Video, video_id)
        if not video:
            raise ResourceNotFoundError(message="Video not found")
        
        if video.hls_url:
            hls_key_prefix = f"hls/{video_id}"
            delete_s3_folder_contents(settings.AWS_STORAGE_BUCKET_NAME, hls_key_prefix)
            
        if video.subtitle_url:
            delete_blob_from_gcs(video.subtitle_url)
        
        await delete_adventure(video.adventure_id, session) # cascade deletes video
        
        return SuccessResponse(
            message="Video deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("Video not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error deleting video: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.patch("/{video_id}")
async def update_video(
    video_id: UUID,
    video_data: VideoUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> VideoResponse:
    
    try:    
        video = await session.get(
            Video,
            video_id,
            options=[
                selectinload(Video.adventure).selectinload(Adventure.series)
            ]
        )
        if not video:
            raise ResourceNotFoundError(message="Video not found")
        
        for field, value in video_data.model_dump(exclude_unset=True).items():
            if field == "thumbnail_url":
                if video.adventure.thumbnail:
                    delete_blob_from_gcs(video.adventure.thumbnail)
                setattr(video.adventure, "thumbnail", value)
            else:
                setattr(video.adventure, field, value)
             
        await session.commit()
        await session.refresh(video, ["adventure"])
        await session.refresh(video.adventure, ["series"])    
        
        return VideoResponse(
            id=video.id,
            adventure_id=video.adventure.id,
            series=video.adventure.series.name if video.adventure.series else None,
            title=video.adventure.title,
            type=video.video_type,
            thumbnail=video.adventure.thumbnail,
            hls_url=video.hls_url,
            duration=video.duration,
        )
        
    except ResourceNotFoundError as e:
        logger.error("Video not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error updating video: {}", str(e), exc_info=True)
        raise InternalServerError()