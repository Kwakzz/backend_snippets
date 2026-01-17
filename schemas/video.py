from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.adventure import AdventurePreview
from app.schemas.series import SeriesResponse
from app.schemas.theme import ThemeSchema


class VideoCreate(BaseModel):
    video_url: str
    thumbnail_url: str
    video_type: str = "full"
    title: str
    series_id: UUID
    
    
class VideoUpdate(BaseModel):
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None
    series_id: Optional[UUID] = None


class VideoResponse(BaseModel):
    id: UUID
    adventure_id: UUID
    title: str
    type: str
    series: Optional[str] = None
    thumbnail: Optional[str]=None
    file_size: Optional[float] = 0
    duration: Optional[int] = 0
    hls_url: Optional[str] = None
    subtitle_url: Optional[str] = None
    message: Optional[str] = None
    
    
class VideoTabDiscoverNewResponse(BaseModel):
    videos: List[AdventurePreview]
    
    
class VideoTabThemesResponse(BaseModel):
    themes: List[ThemeSchema]
    
    
class VideoTabSeriesResponse(BaseModel):
    series: List[SeriesResponse]
    
    
class VideosResponse(BaseModel):
    videos: List[AdventurePreview]
    
    
class VideoStoreMetadata(BaseModel):
    video_id: str 
    hls_url: str 
    duration: int 
    variants: list
    # subtitle_url: str