import os
from pathlib import Path
from typing import List
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.db.session import get_session
from app.db.models import Adventure, QuizQuestion, User, Quiz
from app.core.logging import logger
from app.schemas.quiz import QuestionSchema, QuizSchema, ParseQuizDocRequest
from app.schemas.response import SuccessResponse
from app.services.auth import get_admin_from_token
from app.utils.file import extract_text
from app.utils.gcs import delete_blob_from_gcs, download_file_from_gcs, get_file_metadata_from_gcs_public_url
from app.utils.quiz import format_quiz_text_into_request


router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/parse-from-doc")
async def parse_quiz_from_doc(
    quiz_doc: ParseQuizDocRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> List[QuestionSchema]:  
    
    try: 
        file_extension = get_file_metadata_from_gcs_public_url(quiz_doc.url)["extension"]
        
        TEMP_FOLDER = Path("/tmp")
        TEMP_FOLDER.mkdir(exist_ok=True)
        local_quiz_path = download_file_from_gcs(
            quiz_doc.url,
            os.path.join(TEMP_FOLDER, "quizzes", f"quiz_{str(uuid.uuid4())}.{file_extension}")
        )
        logger.info(f"Downloaded quiz to {local_quiz_path}")
        
        quiz_text = extract_text(
            extension=file_extension,
            file_path=local_quiz_path
        )
        
        list_of_questions = format_quiz_text_into_request(quiz_text)
        
        return [
            QuestionSchema(
                text = question['text'],
                choices = question['choices'],
                correct_answer = question['correct_answer'],
                timestamp_seconds = question.get('timestamp_seconds'),
                question_type = question['question_type'],
            )
            for question in list_of_questions
        ]
        
    except FileNotFoundError as e:
        logger.error("Local quiz path not found. Quiz was likely not downloaded because object doesn't exist in GCS bucket: {}", str(e), exc_info=True)
        raise ResourceNotFoundError(message="File not found")
        
    except Exception as e:
        logger.error("Error parsing quiz from doc: {}", str(e), exc_info=True)
        raise InternalServerError() 
    
    finally:
        if local_quiz_path and os.path.exists(local_quiz_path):
            os.remove(local_quiz_path)
        if quiz_doc.url:
            delete_blob_from_gcs(quiz_doc.url)


@router.post("")
async def create(
    quiz: QuizSchema,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
) -> QuizSchema:
    
    try:    
        adventure = await session.get(Adventure, quiz.adventure_id)
        if not adventure:
            raise ResourceNotFoundError("Adventure not found")
        
        new_quiz = Quiz(adventure_id=quiz.adventure_id)
        session.add(new_quiz)
        await session.flush()  # Ensure new_quiz.id is available

        uploaded_questions = [] 
        
        for q in quiz.questions:
            new_question = QuizQuestion(
                quiz_id=new_quiz.id,
                text=q.text,
                question_type=q.question_type,
                choices=q.choices or [],
                correct_answer=q.correct_answer or [],
                timestamp_seconds=q.timestamp_seconds if q.timestamp_seconds else None
            )
            session.add(new_question)
            uploaded_questions.append(new_question)
        
        await session.commit()
        await session.refresh(new_quiz)

        return QuizSchema(
            id=new_quiz.id,
            adventure_id=new_quiz.adventure_id,
            questions=[
                QuestionSchema(
                    id=str(q.id),
                    text=q.text,
                    choices=q.choices,
                    correct_answer=q.correct_answer,
                    timestamp_seconds=q.timestamp_seconds,
                    question_type=q.question_type
                ) for q in uploaded_questions
            ]
        )
        
    except ResourceNotFoundError as e:
        logger.error("Adventure not found: {}", str(e), exc_info=True)
        raise
        
    except Exception as e:
        logger.error("Error creating quiz: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: UUID, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_admin_from_token)  
):
    """Delete a Quiz by ID

    Args:
        quiz_id (UUID): ID of quiz to be deleted.
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).
        user (User, optional): User must be an admin. Defaults to Depends(get_admin_from_token).

    Raises:
        ResourceNotFoundError: Quiz with quiz_id not found
        InternalServerError: An unexpected error occurs.

    Returns:
        SuccessResponse: Contains a "Quiz deleted" message.
    """
    try:
        
        quiz = await session.get(Quiz, quiz_id)
        if not quiz:
            raise ResourceNotFoundError(message="Quiz not found")
        
        await session.delete(quiz)
        await session.commit()
        logger.info(f"Quiz deleted: {quiz_id}")

        return SuccessResponse(
            message="Quiz deleted",
            data=None
        )
        
    except ResourceNotFoundError as e:
        logger.error("Quiz not found: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error deleting quiz: {}", str(e), exc_info=True)
        raise InternalServerError()