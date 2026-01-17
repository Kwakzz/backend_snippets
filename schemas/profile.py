from typing import Optional
from pydantic import BaseModel
from datetime import date
from uuid import UUID


class ProfileCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    avatar_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    
    
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    avatar_id: Optional[UUID] = None
    

class ProfileResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    avatar_url: Optional[str] = None  
    classroom_name: Optional[str] = None