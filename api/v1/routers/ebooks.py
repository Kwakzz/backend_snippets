from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.db.session import get_session
from app.db.models import Adventure, User, eBook, eBookPage
from app.core.logging import logger
from app.schemas.response import SuccessResponse
from app.schemas.ebook import EbookResponse, EbookStoreMetadata, EbookUpdate, EbookCreate, EbooksResponse, EbookUpdateFile
from app.services.auth import admin_or_ebook_processor, get_user_from_access_token, get_admin_from_token, verify_ebook_processor_token
from app.utils.adventure import create_adventure, delete_adventure
from app.utils.s3 import delete_s3_folder_contents, delete_s3_file
from app.utils.gcs import delete_blob_from_gcs
from app.utils.cloud_task_init import create_cloud_task, CloudTaskQueue, CloudTaskURL
from app.utils.theme import get_themes_assigned_to_ebooks
from app.utils.ebook import get_new_ebooks
from app.utils.notifications import notify_all_users
from app.core.rate_limiter import get_rate_limiter
from app.core.config import settings
from app.services.email import send_email


router = APIRouter(prefix="/ebooks", tags=["Ebooks"])
limiter = get_rate_limiter()

        
@router.post("")
@limiter.limit("3/minute")
async def upload_ebook(
    request: Request,
    ebook_data: EbookCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)
) -> EbookResponse:
    
    try:
        
        new_adventure = await create_adventure(
            session=session, 
            thumbnail_url=ebook_data.thumbnail_url,
            title=ebook_data.title,
        )
        
        ebook = eBook(
            adventure_id=new_adventure.id,
            url=ebook_data.ebook_url
        ) 
        session.add(ebook)
        await session.commit()
        await session.refresh(ebook, ['adventure'])    
        
        task_name = create_cloud_task(
            queue_name=CloudTaskQueue.EBOOK_PROCESSING.value,
            url=CloudTaskURL.EBOOK_PROCESSING.value,
            payload={
                "ebook_id": str(ebook.id),
                "ebook_url": str(ebook_data.ebook_url),
            }
        )
        
        logger.info(f"Cloud Task {task_name} created for eBook processing.")
        
        return EbookResponse(
            id=ebook.id,
            adventure_id=new_adventure.id,
            title=ebook.adventure.title,
            format=ebook.format,
            read_aloud_supported=ebook.read_aloud_supported,
            url=ebook.url,
            message="Ebook processing started"
        )
        
    except Exception as e:
        await session.rollback()
        logger.error("Error creating eBook: {}", str(e), exc_info=True)
        delete_blob_from_gcs(ebook_data.thumbnail_url)
        delete_blob_from_gcs(ebook_data.ebook_url)
        raise InternalServerError()
     
    
@router.post("/store-metadata/create")
async def store_ebook_metadata_after_create(
    metadata: EbookStoreMetadata,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_ebook_processor_token)
):

    try:
        ebook = await session.get(eBook, metadata.ebook_id)
        if not ebook:
            logger.error(f"eBook {metadata.ebook_id} not found.")
            raise ResourceNotFoundError(message="eBook not found")
        
        adventure = await session.get(Adventure, ebook.adventure_id)
        adventure.file_size = round(metadata.file_size, 2)
        
        ebook.page_count = metadata.page_count
        ebook.format = metadata.extension
        
        ebook_pages = []

        for page_number, url in metadata.tts_audio_urls.items():

            ebook_pages.append(
                eBookPage(
                    ebook_id=metadata.ebook_id,
                    page_number=page_number,
                    text=metadata.pages_dict[page_number],
                    tts_url=url
                )
            )
        
        session.add_all(ebook_pages)
        await session.commit()
        
        # Notify users about new ebook content
        title = "New eBook Available!"
        body = f"A new eBook titled '{adventure.title}' is now available to read."
        await notify_all_users(title, body)
        
        # Notify admin about new ebook content
        send_email(
            to_email="wonderspacedapp@gmail.com",
            subject="New eBook Available!",
            body_html=f"<p>Hi Edna,</p><p>The upload of the eBook titled '{adventure.title}' was successful. Users can now read it on the Wonderspaced app.</p><p>Thanks for uploading.</p>"
        )
        
        return EbookResponse(
            id=ebook.id,
            adventure_id=adventure.id,
            thumbnail=adventure.thumbnail,
            title=adventure.title,
            format=ebook.format,
            page_count=ebook.page_count,
            file_size=adventure.file_size,
            url=ebook.url,
            read_aloud_supported=True
        )
        
    except Exception as e:
        logger.error("Error storing eBook metadata: {}", str(e), exc_info=True)
        logger.info("Deleting ebook to avoid inconsistent data...")
        if ebook.url:
            delete_blob_from_gcs(ebook.url)
        if metadata.tts_audio_urls.values():
            for audio_url in metadata.tts_audio_urls.values():
                delete_s3_file(
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    url_or_key=audio_url,
                )
        await delete_adventure(ebook.adventure_id)
        raise 
    
    
@router.get("")
async def get_ebooks(
    q: str = None,
    theme_param: str = None,
    ebooks_offset: int = Query(0),
    ebooks_limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
) -> EbooksResponse:

    try:
        ebooks = await get_new_ebooks(
            session=session,
            offset=ebooks_offset,
            limit=ebooks_limit,
            min_similarity=min_similarity,
            q=q,
            theme_param=theme_param
        )
        
        return EbooksResponse(
            ebooks=ebooks
        )
    
    except Exception as e:
        logger.error("Error getting eBooks: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.delete("/{ebook_id}")
async def delete_ebook(
    ebook_id: UUID, 
    session: AsyncSession = Depends(get_session),
    _: User = Depends(admin_or_ebook_processor),
) -> SuccessResponse:
    
    """Deletes an eBook instance. Deletes the epub/mobi/pdf file from GCS, then the parent adventure (involves deleting the thumbnail from GCS and cascade deleting the eBook instance) 

    Args:
        video_id (UUID): Primary key of eBook
        session (AsyncSession, optional): Database session. Defaults to Depends(get_session).
        user (User, optional): User must be an admin. Defaults to Depends(get_admin_from_token).

    Raises:
        ResourceNotFoundError: eBook not found
        InternalServerError: Unexpected error occurs

    Returns:
        SuccessResponse: Inherits from BaseModel. Contains message and data fields. Message says "eBook deleted."
    """
    try:
        
        ebook = await session.get(eBook, ebook_id)
        if not ebook:
            raise ResourceNotFoundError(message="eBook not found")
        
        if ebook.url:
            delete_blob_from_gcs(ebook.url)
        
        tts_key_prefix = f"tts/{ebook_id}"
        delete_s3_folder_contents(settings.AWS_STORAGE_BUCKET_NAME, tts_key_prefix)
        
        await delete_adventure(ebook.adventure_id, session) # cascade deletes ebook
        
        return SuccessResponse(
            message="eBook deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("eBook not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error deleting eBook: {}", str(e), exc_info=True)
        raise 
    
    
@router.patch("/{ebook_id}")
async def update_ebook(
    ebook_id: UUID,
    ebook_data: EbookUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> EbookResponse:
    
    try:
        ebook = await session.get(
            eBook,
            ebook_id,
            options=[selectinload(eBook.adventure)]
        )
        if not ebook:
            raise ResourceNotFoundError(message="eBook not found")
        
        for field, value in ebook_data.model_dump(exclude_unset=True).items():
            if field == "thumbnail_url":
                if ebook.adventure.thumbnail:
                    delete_blob_from_gcs(ebook.adventure.thumbnail)
                setattr(ebook.adventure, "thumbnail", value)
            else:
                setattr(ebook.adventure, field, value)      
        
        await session.commit()
        await session.refresh(ebook, ['adventure'])

        return EbookResponse(
            id=ebook.id,
            adventure_id=ebook.adventure_id,
            title=ebook.adventure.title,
            format=ebook.format,
            file_size=ebook.adventure.file_size,
            page_count=ebook.page_count,
            read_aloud_supported=ebook.read_aloud_supported,
            url=ebook.url
        )

    except ResourceNotFoundError as e:
        logger.error("eBook not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error updating eBook: {}", str(e), exc_info=True)
        raise InternalServerError()
    

@limiter.limit("3/minute")    
@router.patch("/{ebook_id}/file")
async def update_ebook_file(
    request: Request,
    ebook_id: UUID,
    ebook_data: EbookUpdateFile,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> EbookResponse:
    
    try: 
        ebook = await session.get(
            eBook,
            ebook_id,
            options=[selectinload(eBook.adventure)]
        )
        if not ebook:
            raise ResourceNotFoundError(message="eBook not found")
        
        old_ebook_url = ebook.url
        
        ebook.url = ebook_data.ebook_url
        await session.commit()
        await session.refresh(ebook)
        
        task_name = create_cloud_task(
            queue_name=CloudTaskQueue.EBOOK_UPDATE.value,
            url=CloudTaskURL.EBOOK_UPDATE.value,
            payload={
                "ebook_id": str(ebook.id),
                "ebook_url": str(ebook_data.ebook_url),
            }
        )
        
        logger.info(f"Cloud task created for updating eBook {ebook.id}: {task_name}")
        
        if old_ebook_url:
            logger.info(f"Deleting old eBook file: {old_ebook_url}")
            delete_blob_from_gcs(old_ebook_url)
        
        return EbookResponse(
            id=ebook.id,
            adventure_id=ebook.adventure_id,
            title=ebook.adventure.title,
            format=ebook.format,
            file_size=ebook.adventure.file_size,
            page_count=ebook.page_count,
            read_aloud_supported=ebook.read_aloud_supported,
            url=ebook.url
        )
        
    except ResourceNotFoundError as e:
        logger.error("eBook not found: {}", str(e), exc_info=True)
        delete_blob_from_gcs(ebook_data.ebook_url)
        raise
        
    except Exception as e:
        logger.error("Error updating eBook file: {}", str(e), exc_info=True)
        delete_blob_from_gcs(ebook_data.ebook_url)
        raise InternalServerError()
    
    
@router.post("/store-metadata/update")
async def store_ebook_metadata_after_update(
    metadata: EbookStoreMetadata,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_ebook_processor_token)
) -> EbookResponse:
    
    try:
        ebook = await session.get(eBook, metadata.ebook_id)
        if not ebook:
            logger.error(f"eBook {metadata.ebook_id} not found.")
            raise ResourceNotFoundError(message="eBook not found")
        
        old_ebook_pages_result = await session.exec(
            select(eBookPage)
            .where(eBookPage.ebook_id == ebook.id)
            .order_by(eBookPage.page_number)
        )
        old_ebook_pages = old_ebook_pages_result.all()
        logger.info(f"Old eBook pages stored in memory and pending deletion.")
        
        adventure = await session.get(Adventure, ebook.adventure_id)
        adventure.file_size = round(metadata.file_size, 2)
        
        logger.info(f"Adventure file size updated to {adventure.file_size}")
        
        ebook.page_count = metadata.page_count
        ebook.format = metadata.extension
        
        logger.info(f"eBook page count updated to {ebook.page_count}")
        
        ebook_pages = []

        for page_number, url in metadata.tts_audio_urls.items():
            ebook_pages.append(
                eBookPage(
                    ebook_id=metadata.ebook_id,
                    page_number=page_number,
                    text=metadata.pages_dict[page_number],
                    tts_url=url
                )
            )
        
        session.add_all(ebook_pages)
        await session.commit()
        
        logger.info(f"eBook metadata stored")
        
        # Notify admin about new ebook content
        send_email(
            to_email="wonderspacedapp@gmail.com",
            subject="eBook Updated!",
            body_html=f"<p>Hi Edna,</p><p>The update of the eBook titled '{adventure.title}' was successful. Users can now read it on the Wonderspaced app.</p><p>Thanks for updating.</p>"
        )
        
        # Delete old TTS audio files
        if old_ebook_pages:
            for ebook_page in old_ebook_pages:
                delete_s3_file(
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    url_or_key=ebook_page.tts_url,
                )
                await session.delete(ebook_page)
            await session.commit()
            logger.info(f"Old TTS audio files references deleted from database.")
        
        return EbookResponse(
            id=ebook.id,
            adventure_id=adventure.id,
            thumbnail=adventure.thumbnail,
            title=adventure.title,
            format=ebook.format,
            page_count=ebook.page_count,
            file_size=adventure.file_size,
            url=ebook.url,
            read_aloud_supported=True
        )
        
    except Exception as e:
        logger.error("Error storing eBook metadata: {}", str(e), exc_info=True)
        logger.info("Deleting the tts audio files which we failed to store.")
        if metadata.tts_audio_urls.values():
            for audio_url in metadata.tts_audio_urls.values():
                delete_s3_file(
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    url_or_key=audio_url,
                )
        raise 
        