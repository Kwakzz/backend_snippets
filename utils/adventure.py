from typing import Optional, List
from uuid import UUID
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError
from app.db.models import Adventure, AdventureProgress, Series
from app.core.logging import logger
from app.schemas.adventure import AdventurePreview


from app.utils.gcs import delete_blob_from_gcs


async def create_adventure(
    session: AsyncSession,
    thumbnail_url: str,
    title: str,
    series_id: Optional[UUID] = None,
) -> Adventure:
    
    try: 
        new_adventure = Adventure(
            thumbnail=thumbnail_url,
            title=title,
            series_id=series_id
        )  
        session.add(new_adventure)
        await session.commit()
        
        return new_adventure
    
    except Exception as e:
        logger.error("Error creating adventure: {}", str(e), exc_info=True)
        raise
    
    
async def delete_adventure(
    adventure_id: UUID, 
    session: AsyncSession,
) -> None:
    
    try:
        adventure = await session.get(Adventure, adventure_id)
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")

        delete_blob_from_gcs(adventure.thumbnail)

        await session.delete(adventure)
        await session.commit()
        
    except ResourceNotFoundError as e:
        logger.error("Adventure not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error deleting adventure: {}", str(e), exc_info=True)
        raise
    
    
async def get_or_create_adventure_progress(
    adventure_id: UUID,
    profile_id: UUID,
    session: AsyncSession,
) -> AdventureProgress:
    
    """
    Get or create an AdventureProgress instance. This function is called when a user requests an adventure.
    
    Args:
        adventure_id (UUID): The adventure's ID.
        profile_id (UUID): The ID of the profile continuing or starting an adventure.
        session (AsyncSession): Asynchronous database session
    
    Raises:
        InternalServerError: An unexpected error occurs.
    
    Returns:
        AdventureProgress: The adventure progress instance of profile with ID, profile_id.
    """

    try:
        result = await session.exec(
            select(AdventureProgress).where(
                AdventureProgress.profile_id == profile_id,
                AdventureProgress.adventure_id == adventure_id 
            )
        )
        adventure_progress = result.first()
        if not adventure_progress:
            adventure_progress = AdventureProgress(
                profile_id=profile_id,
                adventure_id=adventure_id,
            )   
            session.add(adventure_progress)
            await session.commit()     
            
        return adventure_progress
    
    except Exception as e:
        logger.error("Error getting or creating AdventureProgress: {}", str(e), exc_info=True)
        raise 


async def get_series_adventures(
    series_name: str,
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
) -> List[AdventurePreview]:
    
    try:

        series_result = await session.exec(
            select(Series).where(
                func.lower(Series.name) == series_name.lower()
            )
        )
        series = series_result.first()
        if not series:
            logger.warning("Series not found: {}", series_name)
            return []
        
        adventures_query = (
            select(Adventure)
            .join(Adventure.series)
            .options(
                selectinload(Adventure.series),
                selectinload(Adventure.ebook),
                selectinload(Adventure.video)
            )
            .where(
                Adventure.series_id == series.id
            )
            .offset(offset)
            .limit(limit)
        )

        if q:
            cleaned_query = " & ".join(q.split())
            adventures_query = adventures_query.where(
                func.to_tsvector('english', Adventure.title).bool_op('@@')(
                    func.plainto_tsquery('english', cleaned_query)
                )
            ).order_by(
                func.ts_rank_cd(
                    func.to_tsvector('english', Adventure.title),
                    func.plainto_tsquery('english', cleaned_query)
                ).desc()
            )

        adventures_result = await session.exec(adventures_query)
        adventures = adventures_result.all()
        
        return [
            AdventurePreview(
                id=adventure.id,
                title=adventure.title,
                thumbnail=adventure.thumbnail,
                series_id=adventure.series_id,
                ebook_id=adventure.ebook.id if adventure.ebook else None,
                video_id=adventure.video.id if adventure.video else None,
                series=adventure.series.name if adventure.series else None,
                created_at=str(adventure.created_at),
            )
            for adventure in adventures
        ]
    
    except Exception as e:
        logger.error("Error getting series' adventures: {}", str(e), exc_info=True)
        raise