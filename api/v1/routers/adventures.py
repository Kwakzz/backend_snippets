from uuid import UUID
from typing import Optional
from sqlmodel import select, func
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.v1.routers.quiz_attempts import get_or_create_quiz_attempt
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.db.models import Adventure, AdventureTheme, Quiz, Theme, User
from app.db.session import get_session
from app.core.logging import logger
from fastapi import APIRouter, Depends, Query
from app.schemas.adventure import AdventureResponse, AssignThemesSchema, UnassignThemeSchema

from app.schemas.quiz import QuestionSchema, QuizSchema
from app.services.auth import get_admin_from_token, get_user_from_access_token
from app.utils.adventure import get_or_create_adventure_progress
from app.utils.ebook import get_tts_urls_for_ebook
from app.utils.file import convert_from_bytes_to_mb
from app.utils.quiz import has_completed_adventure_quiz


router = APIRouter(prefix="/adventures", tags=["Adventures"])
    

@router.get("/{adventure_id}")
async def get_adventure(
    adventure_id: UUID,
    profile_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:
        result = await session.exec(
            select(Adventure)
            .options(
                joinedload(Adventure.ebook),
                joinedload(Adventure.video),
                joinedload(Adventure.series),
                selectinload(Adventure.themes).selectinload(AdventureTheme.theme),
                joinedload(Adventure.quiz).selectinload(Quiz.questions)
            )
            .where(Adventure.id == adventure_id)
        )
           
        adventure = result.first()

        if not adventure:
            raise ResourceNotFoundError(
                message="Adventure not found"
            )

        theme_names = [adventure_theme.theme.name for adventure_theme in adventure.themes]
        
        tts_urls = None
        if adventure.ebook:
             tts_urls = await get_tts_urls_for_ebook(adventure.ebook.id, session)
               
        quiz = None
        if adventure.quiz: 
            quiz = QuizSchema(
                id=adventure.quiz.id,
                questions=[
                    QuestionSchema(
                        id=question.id,
                        text=question.text,
                        choices=question.choices,
                        correct_answer=question.correct_answer,
                        timestamp_seconds=question.timestamp_seconds,
                        question_type=question.question_type,
                    )
                    for question in adventure.quiz.questions
                ],
            )
            
        has_completed_quiz = None
        ongoing_attempt = None            
            
        if profile_id:
            adventure_progress = await get_or_create_adventure_progress(
                adventure_id=adventure_id,
                profile_id=profile_id,
                session=session,
            )
            
            if adventure.quiz:
                ongoing_attempt = await get_or_create_quiz_attempt(
                    profile_id=profile_id,
                    quiz_id=adventure.quiz.id,
                    session=session
                )
                
                has_completed_quiz = await has_completed_adventure_quiz(
                    profile_id=profile_id,
                    quiz_id=adventure.quiz.id,
                    session=session
                )
                
        response = AdventureResponse(
            id=adventure.id,
            title=adventure.title,
            series=adventure.series.name if adventure.series else None,
            video_id=adventure.video.id if adventure.video else None,
            ebook_id=adventure.ebook.id if adventure.ebook else None,
            thumbnail=adventure.thumbnail,
            themes=theme_names,
            size=convert_from_bytes_to_mb(adventure.file_size) if adventure.file_size else 0,
            hls_url=adventure.video.hls_url if adventure.video else None,
            ebook_url=adventure.ebook.url if adventure.ebook else None,
            duration=adventure.video.duration if adventure.video else None,
            ebook_format=adventure.ebook.format if adventure.ebook else None,
            tts_urls=tts_urls if tts_urls else None,
            quiz=quiz,
            ongoing_attempt=ongoing_attempt, # null if profile_id is null
            has_completed_quiz=has_completed_quiz, # null if profile_id is null
            progress_id=adventure_progress.id if profile_id else None,
            is_finished=adventure_progress.is_finished if profile_id else None,
            finished_at=str(adventure_progress.finished_at) if profile_id and adventure_progress.finished_at else None,
            video_stopped_at=adventure_progress.video_stopped_at if profile_id and adventure.video else None,
            last_page_read=adventure_progress.last_page_read if profile_id and adventure.ebook else None,
            saved_for_later=adventure_progress.saved_for_later if profile_id else None,
        )
        return response
    
    except ResourceNotFoundError as e:
        logger.error("Adventure not found: {}", str(e), exc_info=True)
        raise

    except Exception as e:
        logger.error("Error getting adventure: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/assign-themes")
async def assign_themes(
    assign_theme_data: AssignThemesSchema, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> AdventureResponse:
    
    try:
        theme_names = assign_theme_data.name
        adventure_id = assign_theme_data.adventure_id
        
        get_adventure_query = await session.exec(
            select(Adventure)
            .options(
                joinedload(Adventure.ebook),
                joinedload(Adventure.video),
                selectinload(Adventure.themes).selectinload(AdventureTheme.theme)
            )
            .where(Adventure.id == adventure_id)
        )
        adventure = get_adventure_query.first()
        if not adventure:
            raise ResourceNotFoundError(message="Adventure not found")
        
        for theme_name in theme_names:
            get_theme_query = await session.exec(
                select(Theme).where(func.lower(Theme.name) == theme_name.lower())
            )
            theme = get_theme_query.first()
            
            if not theme:
                logger.info(f"Skipped non-existent theme: {theme_name}")
                continue
            
            existing_assignment_query = await session.exec(
                select(AdventureTheme).where(
                    (AdventureTheme.adventure_id == adventure.id) &
                    (AdventureTheme.theme_id == theme.id)
                )
            )
            existing_assignment = existing_assignment_query.first()

            if existing_assignment:
                logger.info(f"Theme '{theme_name}' is already assigned to the adventure.")
                continue
            
            new_adventure_theme = AdventureTheme(
                adventure_id=adventure.id,
                theme_id=theme.id
            )  
            session.add(new_adventure_theme)
            await session.flush()
            
            
        # Remove assigned themes that are not in the new list. Should be case-insensitive.
        theme_names_lower = {name.lower() for name in theme_names}  
        themes_to_remove = [
            adventure_theme for adventure_theme in adventure.themes
            if adventure_theme.theme.name.lower() not in theme_names_lower
        ]

        for adventure_theme in themes_to_remove:
            await session.delete(adventure_theme)
                
        await session.commit()
        await session.refresh(adventure)
        
        theme_names = [adventure_theme.theme.name for adventure_theme in adventure.themes or []]

        return AdventureResponse(
            id=adventure.id,
            title=adventure.title if adventure.title else None,
            video_id=adventure.video.id if adventure.video else None,
            ebook_id=adventure.ebook.id if adventure.ebook else None,
            thumbnail=adventure.thumbnail,
            themes=theme_names,
            size=convert_from_bytes_to_mb(adventure.file_size) if adventure.file_size else 0
        )
        
    except ResourceNotFoundError as e:
        logger.error("Adventure not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error assigning themes: {}", str(e), exc_info=True)
        raise InternalServerError()

    
@router.post("/unassign-theme")
async def unassign_theme(
    request: UnassignThemeSchema, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> AdventureResponse:
    
    try:
        theme_name = request.theme_name
        adventure_id = request.adventure_id
        
        get_theme_query = await session.exec(
            select(Theme)
            .where(func.lower(Theme.name) == theme_name.lower())
        )
        theme = get_theme_query.first()
        if not theme:
            raise ResourceNotFoundError(message="Theme not found")
        
        get_adventure_theme_query = await session.exec(
            select(AdventureTheme)
            .where(
                (AdventureTheme.adventure_id == adventure_id) &
                (AdventureTheme.theme_id == theme.id)
            )
        )
        adventure_theme = get_adventure_theme_query.first()
        if not adventure_theme:
            logger.error("AdventureTheme not found: {}", str(e), exc_info=True)
            raise ResourceNotFoundError(message="This adventure doesn't have the specified theme")
        
        await session.delete(adventure_theme)
        await session.commit()
                
        get_adventure_query = await session.exec(
            select(Adventure)
            .options(
                joinedload(Adventure.ebook),
                joinedload(Adventure.video),
                selectinload(Adventure.themes).selectinload(AdventureTheme.theme)
            )
            .where(Adventure.id == adventure_id)
        )
        adventure = get_adventure_query.first()
        if not adventure:
            logger.error("Adventure not found: {}", str(e), exc_info=True)
            raise ResourceNotFoundError(message="Adventure not found")
        
        theme_names = [adventure_theme.theme.name for adventure_theme in adventure.themes or []]
        
        return AdventureResponse(
            id=adventure.id,
            video_id=adventure.video.id if adventure.video else None,
            ebook_id=adventure.ebook.id if adventure.ebook else None,
            thumbnail=adventure.thumbnail,
            themes=theme_names,
            size=convert_from_bytes_to_mb(adventure.file_size) if adventure.file_size else 0
        )
        
    except ResourceNotFoundError as e:
        raise
        
    except Exception as e:
        logger.error("Error unassigning theme: {}", str(e), exc_info=True)
        raise InternalServerError()