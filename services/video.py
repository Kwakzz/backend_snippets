from app.db.models import Video, Adventure, Series, Theme, AdventureTheme
from app.schemas.adventure import AdventurePreview
from app.db.session import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import joinedload
from typing import List, Optional
from app.core.logging import logger


async def get_new_videos(
    session: AsyncSession,
    offset: int,
    limit: int,
    min_similarity: float = 0.1,
    q: Optional[str] = None,
    series_param: Optional[str] = None,
    theme_param: Optional[str] = None,

) -> List[AdventurePreview]:
    """Get new videos based on search query, series, theme, and pagination

    Args:
        session (AsyncSession): Database session
        offset (int): Offset for pagination
        limit (int): Limit for pagination
        min_similarity (float, optional): Minimum similarity for search query. Defaults to 0.1.
        q (Optional[str], optional): Search query. Defaults to None.
        series_param (Optional[str], optional): Series name. Defaults to None.
        theme_param (Optional[str], optional): Theme name. Defaults to None.

    Returns:
        List[AdventurePreview]: List of AdventurePreview objects
    """

    try:
        videos_query = (
            select(Video)
            .join(Video.adventure)
            .options(
                joinedload(Video.adventure).joinedload(Adventure.series)
            )
            .where(Video.hls_url.isnot(None))
            .order_by(Adventure.created_at.desc())
        )

        if series_param:
            series_result = await session.exec(
                select(Series).where(
                    func.lower(Series.name) == series_param.lower()
                )
            )
            series = series_result.first()
            if series:
                videos_query = videos_query.where(Adventure.series_id == series.id)

        if theme_param:
            theme_result = await session.exec(
                select(Theme).where(
                    func.lower(Theme.name) == theme_param.lower()
                )
            )
            theme = theme_result.first()
            if theme:
                videos_query = videos_query.join(AdventureTheme).where(AdventureTheme.theme_id == theme.id)

        if q:
            cleaned_query = " & ".join([word + ":*" for word in q.split()])
            ts_query = func.to_tsquery('english', cleaned_query)

            videos_query = videos_query.where(
                Adventure.search_vector.op('@@')(ts_query)
            ).order_by(
                func.ts_rank_cd(Adventure.search_vector, ts_query).desc(),
                Adventure.title.asc()
            )
            
        # Apply pagination only if there is no search query
        if not q:
            videos_query = videos_query.offset(offset).limit(limit)
            
        videos_result = await session.exec(videos_query)
        videos = videos_result.all()
        
        videos_list = [
            AdventurePreview(
                id=video.adventure.id,
                title=video.adventure.title,
                series=video.adventure.series.name if video.adventure.series else None,
                video_id=video.id,
                thumbnail=video.adventure.thumbnail,
                created_at=str(video.adventure.created_at)
            )
            for video in videos if video.adventure
        ]
        
        return videos_list
    
    except Exception as e:
        logger.error("Error getting new videos: {}", str(e), exc_info=True)
        raise 