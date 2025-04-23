from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from backend.models.otp import OTPPurpose

class OTPRequest(BaseModel):
    email: EmailStr
    purpose: OTPPurpose

class OTPResponse(BaseModel):
    message: str
    expires_in: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str 