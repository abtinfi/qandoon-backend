from sqlalchemy import Column, Integer, String, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

UTC = timezone.utc
import enum

from backend.database.config import Base
#00
class OrderStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    items = Column(JSON, nullable=False)  # List of sweets with quantities
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    admin_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    user = relationship("User", back_populates="orders") 
    
    #end of the line
    
    #this project is developed by Amir, Abtin and Arshia 