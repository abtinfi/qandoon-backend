from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime
from backend.models.order import OrderStatus

class OrderItem(BaseModel):
    pastry_id: int
    quantity: int

class OrderCreate(BaseModel):
    address: str
    phone_number: str
    items: List[OrderItem]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    address: str
    phone_number: str
    items: List[Dict]
    status: OrderStatus
    admin_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    status: OrderStatus
    admin_message: Optional[str] = None 