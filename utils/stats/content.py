from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import Video, eBook, Theme, Series, Adventure
from app.core.logging import logger
from datetime import datetime


async def get_no_of_videos(session: AsyncSession) -> int:
    """Get the total number of videos"""
    try:
        result = await session.exec(select(func.count(Video.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of videos: {}", str(e), exc_info=True)
        raise


async def get_no_of_ebooks(session: AsyncSession) -> int:
    """Get the total number of ebooks"""
    try:
        result = await session.exec(select(func.count(eBook.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of ebooks: {}", str(e), exc_info=True)
        raise
    

async def get_no_of_themes(session: AsyncSession) -> int:
    try:
        result = await session.exec(select(func.count(Theme.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of themes: {}", str(e), exc_info=True)
        raise


async def get_no_of_series(session: AsyncSession) -> int:
    try:
        result = await session.exec(select(func.count(Series.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of series: {}", str(e), exc_info=True)
        raise


async def get_monthly_new_ebook_rate(session: AsyncSession) -> float:
    """Get the percentage of new ebooks in the past 30 days"""
    try:
        # new ebooks in past month / current ebooks * 100
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        new_ebooks = await session.exec(
            select(func.count(eBook.id))
            .join(eBook.adventure)
            .where(Adventure.created_at >= start_of_month)
        )
        current_ebooks = await get_no_of_ebooks(session)
        if current_ebooks == 0:
            return 0
        return round(new_ebooks.one_or_none() / current_ebooks * 100, 2)
    except Exception as e:
        logger.error("Error getting monthly new ebook rate: {}", str(e), exc_info=True)
        raise
        

async def get_monthly_new_video_rate(session: AsyncSession) -> float:
    """Get the percentage of new videos in the past 30 days"""
    try:
        # new videos in past month / current videos * 100
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        new_videos = await session.exec(
            select(func.count(Video.id))
            .join(Video.adventure)
            .where(Adventure.created_at >= start_of_month)
        )
        current_videos = await get_no_of_videos(session)
        if current_videos == 0:
            return 0
        return round(new_videos.one_or_none() / current_videos * 100, 2)
    except Exception as e:
        logger.error("Error getting monthly new video rate: {}", str(e), exc_info=True)
        raise