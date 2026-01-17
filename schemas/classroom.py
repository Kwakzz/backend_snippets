from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.schemas.profile import ProfileResponse


class ClassroomCreate(BaseModel): 
    name: str
    

class ClassroomResponse(BaseModel):
    id: UUID
    name: str
    code: str
    teacher_name: Optional[str] = None
    student_count: Optional[int] = None
    

class ClassroomUpdate(BaseModel):
    name: str
    
    
class ClassroomDelete(BaseModel):
    ids: List[str]