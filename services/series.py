from sqlmodel import select
from uuid import UUID
from app.db.session import AsyncSession
from app.db.models import Series, Adventure
from app.core.logging import logger
from typing import List
from app.schemas.series import SeriesResponse, SeriesContentType


async def get_video_series(
    session: AsyncSession,
) -> List[SeriesResponse]:
    try:
        series_query = (
            select(Series)
            .where(Series.content == "video")
        )
        
        series_result = await session.exec(series_query)
        series = series_result.all()
        
        return [
            SeriesResponse(
                id=s.id,
                name=s.name,
                content=SeriesContentType(s.content)
            )
            for s in series
        ]
    
    except Exception as e:
        logger.error("Error getting video series: {}", str(e), exc_info=True)
        raise


async def get_series_adventures_count(
    series_id: UUID,
    session: AsyncSession
) -> int:
    try:
        adventures_query = (
            select(Adventure)
            .where(Adventure.series_id == series_id)
        )
                
        adventures_result = await session.exec(adventures_query)
        adventures = adventures_result.all()
        
        return len(adventures)
    
    except Exception as e:
        logger.error("Error getting series adventures count: {}", str(e), exc_info=True)
        raise
    
    