from sqlmodel import select, func

from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import AdventureProgress, QuizAttempt, Adventure, AdventureTheme, Theme, Series
from app.core.logging import logger
from uuid import UUID
from typing import Optional


async def get_number_of_quiz_attempts(
    profile_id: UUID,
    session: AsyncSession
) -> int:
    try:
        result = await session.exec(
            select(func.count(QuizAttempt.id))
            .where(
                (QuizAttempt.profile_id == profile_id)
            )
        )
        count = result.first()
        return count if count is not None else 0
    except Exception as e:
        raise
    
    
async def get_favourite_theme(
    profile_id: UUID,
    session: AsyncSession
) -> Optional[str]:
    """
    Get the most frequent theme in a user's adventure progress records.
    
    Args:
        profile_id: The ID of the user profile
        session: Database session
        
    Returns:
        The name of the most frequent theme, or None if no progress records exist
    """
    try:
        query = (
            select(
                Theme.name,
                func.count(AdventureProgress.id).label('count')
            )
            .select_from(AdventureProgress)
            .join(Adventure, Adventure.id == AdventureProgress.adventure_id)
            .join(AdventureTheme, AdventureTheme.adventure_id == Adventure.id)
            .join(Theme, Theme.id == AdventureTheme.theme_id)
            .where(AdventureProgress.profile_id == profile_id)
            .group_by(Theme.name)
            .order_by(func.count(AdventureProgress.id).desc())
            .limit(1)
        )
        
        result = await session.exec(query)
        most_common_theme = result.first()
        
        return most_common_theme[0] if most_common_theme else None
        
    except Exception as e:
        logger.error(f"Error getting favorite theme for profile {profile_id}: {str(e)}")
        raise
    
    
async def get_favourite_series(
    profile_id: UUID,
    session: AsyncSession
) -> Optional[str]:
    """
    Get the most frequent series in a user's adventure progress records.
    
    Args:
        profile_id: The ID of the user profile
        session: Database session
        
    Returns:
        The name of the most frequent series, or None if no progress records exist
    """
    try:
        query = (
            select(
                Series.name,
                func.count(AdventureProgress.id).label('count')
            )
            .select_from(AdventureProgress)
            .join(Adventure, Adventure.id == AdventureProgress.adventure_id)
            .join(Series, Series.id == Adventure.series_id)
            .where(AdventureProgress.profile_id == profile_id)
            .group_by(Series.name)
            .order_by(func.count(AdventureProgress.id).desc())
            .limit(1)
        )
        
        result = await session.exec(query)
        most_common_series = result.first()
        
        return most_common_series[0] if most_common_series else None
        
    except Exception as e:
        logger.error(f"Error getting favorite series for profile {profile_id}: {str(e)}")
        raise