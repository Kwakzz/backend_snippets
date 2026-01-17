from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.quiz import QuizSchema
from app.schemas.quiz_attempt import QuizAttemptResponseSchema


class EbookPageSchema(BaseModel):
    page_number: int
    tts_url: str
    
    
class SaveForLaterRequest(BaseModel):
    profile_id: UUID
    save_for_later: bool
    

class AdventurePreview(BaseModel):
    id: UUID
    title: Optional[str] = None
    series: Optional[str] = None
    video_id: Optional[UUID] = None
    ebook_id: Optional[UUID] = None
    thumbnail: Optional[str] = None
    created_at: Optional[str] = None
    

class AdventureResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    video_id: Optional[UUID] = None
    ebook_id: Optional[UUID] = None
    thumbnail: Optional[str] = None
    series: Optional[str] = None
    themes: Optional[List[str]] = []
    size: Optional[float] = 0
    hls_url: Optional[str] = None
    subtitle_url: Optional[str] = None
    duration: Optional[int] = 0
    ebook_url: Optional[str] = None
    ebook_format: Optional[str] = None
    tts_urls: Optional[List[EbookPageSchema]] = None
    quiz: Optional[QuizSchema] = None
    ongoing_attempt: Optional[QuizAttemptResponseSchema] = None # for when a profile id is included as a query param in getting an adventure
    has_completed_quiz: Optional[bool] = None
    progress_id: Optional[UUID] = None
    is_finished: Optional[bool] = None
    finished_at: Optional[str] = None 
    video_stopped_at: Optional[int] = None
    last_page_read: Optional[int] = None
    saved_for_later: Optional[bool] = None
   
   
class AdventureProgressSchema(BaseModel):
    progress_id: Optional[UUID] = None
    video_stopped_at: Optional[int] = None
    last_page_read: Optional[int] = None
    is_finished: Optional[bool] = False
    saved_for_later: Optional[bool] = False
    finished_at: Optional[str] = None 
    
    
class AssignThemesSchema(BaseModel):
    name: List[str]
    adventure_id: UUID
    
    
class UnassignThemeSchema(BaseModel):
    theme_name: str
    adventure_id: UUID