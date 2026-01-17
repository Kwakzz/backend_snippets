from typing import List
from pydantic import BaseModel
from app.schemas.adventure import AdventurePreview
    
    
class ExploreTabVideosResponse(BaseModel):
    videos: List[AdventurePreview]
    

class ExploreTabEbooksResponse(BaseModel):
    ebooks: List[AdventurePreview]
    
    
class ExploreTabInProgressResponse(BaseModel):
    adventures: List[AdventurePreview]
    
    
class ExploreTabDiysResponse(BaseModel):
    adventures: List[AdventurePreview]
    