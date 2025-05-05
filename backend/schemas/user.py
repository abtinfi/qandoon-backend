from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    password: str
    is_admin: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
