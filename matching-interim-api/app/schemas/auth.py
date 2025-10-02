# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime
import uuid

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: Dict

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    nom: Optional[str]
    prenom: Optional[str]
    role: str
    client_id: str
    
    class Config:
        from_attributes = True

# ==========================================