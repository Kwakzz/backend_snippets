from enum import Enum
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class EmailPasswordCreds(BaseModel):
    email: EmailStr
    password: str
    
    
class ClassCodeLogin(BaseModel):
    class_code: str


class GoogleUser(BaseModel):
    id_token: str
    

class ChangePasswordSchema(BaseModel):
    password1: str
    password2: str   


class VerifyTokenSchema(BaseModel):
    token: str
    
    
class SSOProvider(Enum):
    GOOGLE = "google"