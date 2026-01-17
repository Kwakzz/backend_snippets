from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import UserProfile, User, QuizAttempt
from app.core.logging import logger
from datetime import datetime, timedelta


def get_start_of_week() -> datetime:
    """Get the start of the current week (Monday at 00:00:00)"""
    today = datetime.now()
    # Monday is 0 and Sunday is 6 in isoweekday()
    days_since_monday = today.isoweekday() - 1
    return (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)


async def get_no_of_accounts(session: AsyncSession) -> int:
    """Get the total number of accounts"""
    try:
        result = await session.exec(select(func.count(User.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of accounts: {}", str(e), exc_info=True)
        raise


async def get_no_of_profiles(session: AsyncSession) -> int:
    """Get the total number of profiles"""
    try:
        result = await session.exec(select(func.count(UserProfile.id)))
        return result.one_or_none()
    except Exception as e:
        logger.error("Error getting number of profiles: {}", str(e), exc_info=True)
        raise


async def get_weekly_new_account_rate(session: AsyncSession) -> float:
    """Get the percentage of new accounts since the start of the current week (Monday)"""
    try:
        start_of_week = get_start_of_week()
        
        # new accounts since start of week / current accounts * 100
        new_accounts = await session.exec(
            select(func.count(User.id))
            .where(User.created_at >= start_of_week)
        )
        current_accounts = await get_no_of_accounts(session)
        if current_accounts == 0:
            return 0
        return round(new_accounts.one_or_none() / current_accounts * 100, 2)
    except Exception as e:
        logger.error("Error getting weekly new account rate: {}", str(e), exc_info=True)
        raise
        

async def get_monthly_new_account_rate(session: AsyncSession) -> float:
    """Get the percentage of new accounts created since the start of the current month"""
    try:
        # Get the first day of the current month at 00:00:00
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # new accounts since start of month / current accounts * 100
        new_accounts = await session.exec(
            select(func.count(User.id))
            .where(User.created_at >= start_of_month)
        )
        current_accounts = await get_no_of_accounts(session)
        if current_accounts == 0:
            return 0
        return round(new_accounts.one_or_none() / current_accounts * 100, 2)
    except Exception as e:
        logger.error("Error getting monthly new account rate: {}", str(e), exc_info=True)
        raise

        
async def get_average_age(session: AsyncSession) -> float:
    """Get the average age of users in years
    
    Args:
        session (AsyncSession): Database session
        
    Returns:
        float: Average age in years, rounded to 2 decimal places
    """
    try:
        # Get current date
        current_date = datetime.now().date()
        
        # Calculate age in years using PostgreSQL's date_part function
        # This is more accurate than calculating it in Python
        result = await session.exec(
            select(
                func.avg(
                    func.date_part('year', func.age(current_date, UserProfile.date_of_birth))
                )
            )
        )
        
        avg_age = result.one_or_none()
        return round(float(avg_age), 2) if avg_age is not None else 0.0
        
    except Exception as e:
        logger.error("Error getting average age: {}", str(e), exc_info=True)
        raise


async def get_no_of_active_learners(session: AsyncSession) -> int:
    """Get the number of profiles that have more than one quiz attempt
    
    Args:
        session (AsyncSession): Database session
        
    Returns:
        int: Number of profiles with more than one quiz attempt
    """
    try:
        # Subquery to count quiz attempts per profile
        stmt = (
            select(
                QuizAttempt.profile_id,
                func.count(QuizAttempt.id).label('attempt_count')
            )
            .group_by(QuizAttempt.profile_id)
            .having(func.count(QuizAttempt.id) > 1)
            .subquery()
        )
        
        # Count distinct profiles with more than one attempt
        result = await session.exec(
            select(func.count()).select_from(stmt)
        )
        
        return result.one_or_none()
        
    except Exception as e:
        logger.error("Error getting number of active learners: {}", str(e), exc_info=True)
        raise