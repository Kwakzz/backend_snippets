from pydantic import BaseModel
from typing import Optional


class AdventureURLGet(BaseModel):
    filename: str
    thumbnail: Optional[str] = None
    
    
class ThumbnailURLGet(BaseModel):
    thumbnail: str
    
    
class AvatarURLGet(BaseModel):
    filename: str
    
    
class ThemeIconURLGet(BaseModel):
    icon_name: str
    
    
class QuizURLGet(BaseModel):
    filename: str