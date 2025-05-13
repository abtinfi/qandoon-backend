from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)

class UserUpdateUsername(BaseModel):
    name: str

