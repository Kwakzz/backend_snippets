from typing import List
from uuid import UUID
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.models import Theme, AdventureTheme, Adventure, Video, eBook
from app.core.logging import logger
from app.schemas.theme import ThemeSchema


async def theme_exists(
    session: AsyncSession,
    name: str
) -> bool:
    
    try:
        existing_theme_query = await session.exec(
            select(Theme).where(func.lower(Theme.name) == name.lower())
        )
        existing_theme = existing_theme_query.first()
        
        if existing_theme:
            return True
        
        return False
    
    except Exception as e:
        logger.error("Error checking if theme exists: {}", str(e), exc_info=True)
        raise


async def get_themes_assigned_to_videos(
    session: AsyncSession,
    offset: int,
    limit: int,
) -> List[ThemeSchema]:
    try:
        
        themes_query = (
            select(Theme)
            .join(AdventureTheme, Theme.id == AdventureTheme.theme_id)
            .join(Adventure, AdventureTheme.adventure_id == Adventure.id)
            .join(Video, Video.adventure_id == Adventure.id)
            .where(Video.id.isnot(None))
            .distinct()
            .offset(offset)
            .limit(limit)
        )
        
        themes_result = await session.exec(themes_query)
        themes = themes_result.all()
        
        return [
            ThemeSchema(
                id=theme.id,
                name=theme.name,
                icon=theme.icon if theme.icon else None
            )
            for theme in themes
        ]
    
    except Exception as e:
        logger.error("Error getting themes assigned to video: {}", str(e), exc_info=True)
        raise


async def get_themes_assigned_to_ebooks(
    session: AsyncSession,
    offset: int,
    limit: int,
) -> List[ThemeSchema]:
    try:
            
        themes_query = (
            select(Theme)
            .join(AdventureTheme, Theme.id == AdventureTheme.theme_id)
            .join(Adventure, AdventureTheme.adventure_id == Adventure.id)
            .join(eBook, eBook.adventure_id == Adventure.id)
            .where(eBook.id.isnot(None))
            .distinct()
            .offset(offset)
            .limit(limit)
        )
        
        themes_result = await session.exec(themes_query)
        themes = themes_result.all()
        
        return [
            ThemeSchema(
                id=theme.id,
                name=theme.name,
                icon=theme.icon if theme.icon else None
            )
            for theme in themes
        ]
    
    except Exception as e:
        logger.error("Error getting themes assigned to ebook: {}", str(e), exc_info=True)
        raise


async def get_adventures_assigned_to_theme_count(
    theme_id: UUID,
    session: AsyncSession
) -> int:
    try:
        adventures_query = (
            select(AdventureTheme)
            .where(AdventureTheme.theme_id == theme_id)
        )
        adventures_result = await session.exec(adventures_query)
        adventures = adventures_result.all()
        return len(adventures)
    
    except Exception as e:
        logger.error("Error getting adventures assigned to theme: {}", str(e), exc_info=True)
        raise
    