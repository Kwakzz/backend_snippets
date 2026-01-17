from typing import List
from pydantic import BaseModel
from uuid import UUID


class AvatarsCreate(BaseModel):
    urls: List[str]


class AvatarResponse(BaseModel):
    id: UUID
    url: str
    
    class Config:
        from_attributes = True