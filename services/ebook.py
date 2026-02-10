from typing import List, Optional

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi_cache.decorator import cache

from app.schemas.adventure import EbookPageSchema
from app.schemas.adventure import AdventurePreview
from app.db.models import eBookPage, eBook, Adventure, Theme, AdventureTheme
from app.services.s3 import delete_s3_file
from app.core.logging import logger
from app.core.config import settings


@cache(expire=300)    
async def get_tts_urls_for_ebook(
    ebook_id: str,
    session: AsyncSession
) -> List[EbookPageSchema]:
    
    try:
        result = await session.exec(
            select(eBookPage.page_number, eBookPage.tts_url)
            .where(eBookPage.ebook_id == ebook_id)
            .order_by(eBookPage.page_number)
        )
        rows = result.all()
        return [
            EbookPageSchema(
                page_number=page, 
                tts_url=url
            ) for page, url in rows
        ]
    
    except Exception as e:
        raise


async def get_new_ebooks(
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    theme_param: Optional[str] = None,
) -> List[AdventurePreview]:

    try:
        ebooks_query = (
            select(eBook)
            .join(eBook.adventure)
            .options(
                joinedload(eBook.adventure).joinedload(Adventure.series))
            .where(eBook.url.isnot(None))
            .order_by(Adventure.created_at.desc())
        )

        if theme_param:
            theme_result = await session.exec(
                select(Theme).where(
                    func.lower(Theme.name) == theme_param.lower()
                )
            )
            theme = theme_result.first()
            if theme:
                ebooks_query = ebooks_query.join(AdventureTheme).where(AdventureTheme.theme_id == theme.id)

        if q:
            cleaned_query = " & ".join([word + ":*" for word in q.split()])
            ts_query = func.to_tsquery('english', cleaned_query)

            ebooks_query = ebooks_query.where(
                Adventure.search_vector.op('@@')(ts_query)
            ).order_by(
                func.ts_rank_cd(Adventure.search_vector, ts_query).desc(),
                Adventure.title.asc()
            )

        # Apply pagination only if there is no search query
        if not q:
            ebooks_query = ebooks_query.offset(offset).limit(limit)
            
        ebooks_result = await session.exec(ebooks_query)
        ebooks = ebooks_result.all()
        
        ebooks_list = [
            AdventurePreview(
                id=ebook.adventure.id,
                title=ebook.adventure.title,
                ebook_id=ebook.id,
                thumbnail=ebook.adventure.thumbnail,
                created_at=str(ebook.adventure.created_at)
            )
            for ebook in ebooks if ebook.adventure
        ]
        
        return ebooks_list
        
    except Exception as e:
        logger.error("Error getting new ebooks: {}", str(e), exc_info=True)
        raise
    
    
async def delete_tts_audios(
    ebook_id: str,
    session: AsyncSession
) -> None:
    try:
        result = await session.exec(
            select(eBookPage)
            .where(eBookPage.ebook_id == ebook_id)
            .order_by(eBookPage.page_number)
        )
        rows = result.all()
        
        for page in rows:
            delete_s3_file(settings.AWS_STORAGE_BUCKET_NAME, page.tts_url)
            await session.delete(page)
            
        await session.commit()
    except Exception as e:
        logger.error("Error deleting TTS for ebook: {}", str(e), exc_info=True)
        raise
   
        