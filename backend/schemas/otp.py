from pydantic import BaseModel, EmailStr
import enum
class OTPPurpose(enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    
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

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str
