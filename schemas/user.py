from enum import Enum
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_family_account: Optional[bool] = None
    is_teacher_account: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school: Optional[str] = None
     

class UserResponse(BaseModel):
    id: UUID
    email: str
    token: str = None
    created_at: str = None
    email_verified_at: Optional[str] = None
    is_new: Optional[bool] = None # useful for determining whether a user is new when opt for Google Auth
    is_admin: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school: Optional[str] = None
    is_family_account: Optional[bool] = None
    is_teacher_account: Optional[bool] = None
    
    
class ClassCodeLoginResponse(BaseModel):
    token: str
    class_code: str
    class_id: UUID
    class_name: str
    teacher_name: str
    

class SendEmailSchema(BaseModel):
    email: EmailStr
    
    
class EmailSuccess(BaseModel):
    message: str = "Success. Check your email."