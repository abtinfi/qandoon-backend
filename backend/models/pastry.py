from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from backend.database.config import Base

class Pastry(Base):
    __tablename__ = "pastries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    image_url = Column(String)
    price = Column(Float)
    stock = Column(Float) #Changed from integer to float because it is based on kilograms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Integer, default=0)  # 0: not deleted, 1: deleted
    
    
    #end of the line 