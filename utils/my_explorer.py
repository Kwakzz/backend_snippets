from uuid import UUID
from typing import Optional, List

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import func, select
from sqlalchemy.orm import selectinload

from app.db.models import AdventureProgress, QuizAttempt, Adventure
from app.schemas.quiz_attempt import QuizAttemptStatus
from app.schemas.adventure import AdventurePreview


async def get_quizzes_done_count(
    profile_id: UUID,
    session: AsyncSession
) -> int:
    try:
        result = await session.exec(
            select(func.count(func.distinct(QuizAttempt.quiz_id)))
            .where(
                (QuizAttempt.profile_id == profile_id) &
                (QuizAttempt.status == QuizAttemptStatus.FINISHED.value)
            )
        )
        count = result.first()
        return count if count is not None else 0
    except Exception as e:
        raise
    
    
async def get_ebooks_read_count(
    profile_id: UUID,
    session: AsyncSession
) -> bool:
    
    try:
        
        result = await session.exec(
            select(func.count(AdventureProgress.id))
            .where(
                (AdventureProgress.profile_id == profile_id) &
                (AdventureProgress.finished_at != None) &
                (AdventureProgress.last_page_read != None)
            )
        )
        count = result.first()
        if count is not None:
            return count
        else:
            return 0
        
    except Exception as e:
        raise
    
    
async def get_videos_watched_count(
    profile_id: UUID,
    session: AsyncSession
) -> bool:
    
    try:
        
        result = await session.exec(
            select(func.count(AdventureProgress.id))
            .where(
                (AdventureProgress.profile_id == profile_id) &
                (AdventureProgress.finished_at != None) &
                (AdventureProgress.video_stopped_at != None)
            )
        )
        count = result.first()
        if count is not None:
            return count
        else:
            return 0
        
    except Exception as e:
        raise
    
    
async def get_adventures_done_count(
    profile_id: UUID,
    session: AsyncSession
) -> bool:
    
    try:
        
        result = await session.exec(
            select(func.count(AdventureProgress.id))
            .where(
                (AdventureProgress.profile_id == profile_id) &
                (AdventureProgress.finished_at != None)
            )
        )
        count = result.first()
        if count is not None:
            return count
        else:
            return 0
        
    except Exception as e:
        raise
    
    
async def get_explorer_adventures(
    profile_id: UUID,
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    content_type: Optional[str] = None
):
    try:
        
        adventures_query = (
            select(AdventureProgress)
            .options(
                selectinload(AdventureProgress.adventure).selectinload(Adventure.ebook),
                selectinload(AdventureProgress.adventure).selectinload(Adventure.video),
                selectinload(AdventureProgress.adventure).selectinload(Adventure.series),
            )
            .where(AdventureProgress.profile_id == profile_id)
        )

        if q:
            cleaned_query = " & ".join([word + ":*" for word in q.split()])
            ts_query = func.to_tsquery('english', cleaned_query)

            adventures_query = adventures_query.where(
                Adventure.search_vector.op('@@')(ts_query)
            ).order_by(
                func.ts_rank_cd(Adventure.search_vector, ts_query).desc(),
                Adventure.title.asc()
            )

        # Apply pagination only if there is no search query
        if not q:
            adventures_query = adventures_query.offset(offset).limit(limit)
            
        if content_type:
            if content_type == "video":
                adventures_query = adventures_query.where(AdventureProgress.adventure.has(Adventure.video != None))
            elif content_type == "ebook":
                adventures_query = adventures_query.where(AdventureProgress.adventure.has(Adventure.ebook != None))
            
        adventures_result = await session.exec(adventures_query)
        adventure_progress_records = adventures_result.all()
        
        return adventure_progress_records
    
    except Exception as e:
        raise


async def get_adventures_in_progress(
    profile_id: UUID,
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    content_type: Optional[str] = None
) -> List[AdventurePreview]:
    try:
        
        adventure_progress_records = await get_explorer_adventures(
            profile_id=profile_id,
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q,
            content_type=content_type
        )
        
        adventures_list = [
            AdventurePreview(
                id=record.adventure_id,
                video_id=record.adventure.video.id if record.adventure.video else None,
                ebook_id=record.adventure.ebook.id if record.adventure.ebook else None,
                thumbnail=record.adventure.thumbnail,
            )
            for record in adventure_progress_records if (record.last_page_read or record.video_stopped_at) and not record.is_finished
        ]
        
        return adventures_list
    
    except Exception as e:
        raise
        
    
async def get_adventures_finished(
    profile_id: UUID,
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    content_type: Optional[str] = None
) -> List[AdventurePreview]:
    try:
        
        adventure_progress_records = await get_explorer_adventures(
            profile_id=profile_id,
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q,
            content_type=content_type
        )
        
        adventures_list = [
            AdventurePreview(
                id=record.adventure_id,
                video_id=record.adventure.video.id if record.adventure.video else None,
                ebook_id=record.adventure.ebook.id if record.adventure.ebook else None,
                thumbnail=record.adventure.thumbnail,
            )
            for record in adventure_progress_records if record.is_finished
        ]
        
        return adventures_list
    
    except Exception as e:
        raise
    
    
async def get_adventures_saved(
    profile_id: UUID,
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    content_type: Optional[str] = None
) -> List[AdventurePreview]:
    try:
        
        adventure_progress_records = await get_explorer_adventures(
            profile_id=profile_id,
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q,
            content_type=content_type
        )
        
        adventures_list = [
            AdventurePreview(
                id=record.adventure_id,
                video_id=record.adventure.video.id if record.adventure.video else None,
                ebook_id=record.adventure.ebook.id if record.adventure.ebook else None,
                thumbnail=record.adventure.thumbnail,
            )
            for record in adventure_progress_records if record.saved_for_later
        ]
        
        return adventures_list
    
    except Exception as e:
        raise