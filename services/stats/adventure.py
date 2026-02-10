from uuid import UUID
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError
from app.db.models import Adventure, AdventureProgress, Quiz, QuizAttempt
from app.schemas.quiz_attempt import QuizAttemptStatus
from app.core.logging import logger
from sqlalchemy import or_
from typing import Optional



async def get_no_of_views(
    adventure_id: UUID,
    session: AsyncSession,
) -> int:
    try:
        adventure = await session.get(
            Adventure, 
            adventure_id,
            options=[selectinload(Adventure.adventure_progress_records)]
        )
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        query = (
            select(func.count(AdventureProgress.id))
            .where(
                AdventureProgress.adventure_id == adventure_id,
                or_(
                    AdventureProgress.last_page_read.isnot(None),
                    AdventureProgress.video_stopped_at.isnot(None)
                )
            )
        )
        
        result = await session.exec(query)
        no_of_views = result.first()
        
        return no_of_views
    
    except Exception as e:
        logger.error("Error getting no of views: {}", str(e), exc_info=True)
        raise
    
    
async def get_no_of_completions(
    adventure_id: UUID,
    session: AsyncSession,
) -> int:
    try:
        adventure = await session.get(
            Adventure, 
            adventure_id,
            options=[selectinload(Adventure.adventure_progress_records)]
        )
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        query = (
            select(func.count(AdventureProgress.id))
            .where(
                AdventureProgress.adventure_id == adventure_id,
                AdventureProgress.is_finished == True
            )
        )
        
        result = await session.exec(query)
        no_of_completions = result.first()
        
        return no_of_completions
    
    except Exception as e:
        logger.error("Error getting number of completions: {}", str(e), exc_info=True)
        raise
    
    
async def get_no_of_saved_for_later(
    adventure_id: UUID,
    session: AsyncSession,
) -> int:
    try:
        adventure = await session.get(
            Adventure, 
            adventure_id,
            options=[selectinload(Adventure.adventure_progress_records)]
        )
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        query = (
            select(func.count(AdventureProgress.id))
            .where(
                AdventureProgress.adventure_id == adventure_id,
                AdventureProgress.saved_for_later == True
            )
        )
        
        result = await session.exec(query)
        no_of_saved_for_later = result.first()
        
        return no_of_saved_for_later
    
    except Exception as e:
        logger.error("Error getting number of saved for later: {}", str(e), exc_info=True)
        raise
    

async def get_no_of_quiz_attempts_started(
    adventure_id: UUID,
    session: AsyncSession,
) -> int:
    try:
        quiz_result = await session.exec(
            select(Quiz)
            .where(
                Quiz.adventure_id == adventure_id
            )
            .options(selectinload(Quiz.attempts))
        )
        quiz = quiz_result.first()
        if not quiz:
            return 0
        
        query = (
            select(func.count(QuizAttempt.id))
            .where(
                QuizAttempt.quiz_id == quiz.id,
            )
        )
        
        result = await session.exec(query)
        no_of_quiz_attempts_started = result.first()
        
        return no_of_quiz_attempts_started
    
    except Exception as e:
        logger.error("Error getting number of quiz attempts started: {}", str(e), exc_info=True)
        raise
    
    
async def get_no_of_quiz_attempts_completed(
    adventure_id: UUID,
    session: AsyncSession,
) -> int:
    try:
        quiz_result = await session.exec(
            select(Quiz)
            .where(
                Quiz.adventure_id == adventure_id
            )
            .options(selectinload(Quiz.attempts))
        )
        
        quiz = quiz_result.first()
        if not quiz:
            return 0
        
        query = (
            select(func.count(QuizAttempt.id))
            .where(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.status == QuizAttemptStatus.FINISHED.value
            )
        )
        
        result = await session.exec(query)
        no_of_quiz_attempts_completed = result.first()
        
        return no_of_quiz_attempts_completed
    
    except Exception as e:
        logger.error("Error getting number of quiz attempts completed: {}", str(e), exc_info=True)
        raise
    

async def get_average_watch_time(
    adventure_id: UUID,
    session: AsyncSession,
) -> Optional[float]:
    try:
        adventure = await session.get(
            Adventure, 
            adventure_id,
            options=[selectinload(Adventure.adventure_progress_records)]
        )
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        query = (
            select(func.avg(AdventureProgress.video_stopped_at))
            .where(
                AdventureProgress.adventure_id == adventure_id,
                AdventureProgress.video_stopped_at.isnot(None)
            )
        )
        
        result = await session.exec(query)
        average_watch_time = result.first()
        
        return round(average_watch_time, 2) if average_watch_time else None
    
    except Exception as e:
        logger.error("Error getting average watch time: {}", str(e), exc_info=True)
        raise
    

async def get_average_no_of_pages_read(
    adventure_id: UUID,
    session: AsyncSession,
) -> Optional[float]:
    try:
        adventure = await session.get(
            Adventure, 
            adventure_id,
            options=[selectinload(Adventure.adventure_progress_records)]
        )
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        query = (
            select(func.avg(AdventureProgress.last_page_read))
            .where(
                AdventureProgress.adventure_id == adventure_id,
                AdventureProgress.last_page_read.isnot(None)
            )
        )
        
        result = await session.exec(query)
        average_no_of_pages_read = result.first()
        
        return round(average_no_of_pages_read, 2) if average_no_of_pages_read else None
    
    except Exception as e:
        logger.error("Error getting average no of pages read: {}", str(e), exc_info=True)
        raise
    

