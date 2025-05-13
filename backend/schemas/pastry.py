from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class PastryBase(BaseModel):
    name: str
    description: str
    image_url: str
    price: float
    stock: int

class PastryCreate(PastryBase):
    pass

class PastryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class PastryResponse(PastryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) 