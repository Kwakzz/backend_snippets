from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.adventure import AdventurePreview
from app.schemas.theme import ThemeSchema


class EbookCreate(BaseModel):
    ebook_url: str
    thumbnail_url: str
    title: str    
    series_id: Optional[UUID] = None


class EbookUpdate(BaseModel):
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None
    series_id: Optional[UUID] = None
    

class EbookUpdateFile(BaseModel):
    ebook_url: str


class EbookResponse(BaseModel):
    id: UUID
    adventure_id: UUID
    title: str
    series: Optional[str] = None
    thumbnail: Optional[str]=None
    file_size: Optional[float] = 0
    url: Optional[str] = None
    format: Optional[str] = None
    read_aloud_supported: Optional[bool] = True
    page_count: Optional[int]=0
    message: Optional[str] = None
    
    
class EbookTabDiscoverNewResponse(BaseModel):
    ebooks: List[AdventurePreview]
    

class EbookTabThemesResponse(BaseModel):
    themes: List[ThemeSchema]
    

class EbooksResponse(BaseModel):
    ebooks: List[AdventurePreview]
    
    
class EbookStoreMetadata(BaseModel):
    ebook_id: str
    page_count: int
    extension: str
    file_size: float
    tts_audio_urls: dict[int, str] #<page_number, tts_url>
    pages_dict: dict[int, str] #<page_number, text>