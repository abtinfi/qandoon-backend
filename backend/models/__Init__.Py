# backend/models/__init__.py

# Import the SQLAlchemy Base class
# Use relative import because database is a sibling package to models
from ..database.config import Base

# Import all your ORM model classes
# This is crucial for SQLAlchemy to register them properly
# Use relative import because user.py, order.py, pastry.py are sibling modules
from .user import User
from .order import Order
from .pastry import Pastry

# Add any other models you create in this directory here:
# from .other_model import OtherModel

# Optional: Define __all__ to explicitly state what is available
# when someone does 'from backend.models import *'
__all__ = [
    "Base",
    "User",
    "Order",
    "Pastry",
    # Add names of other models here
]

print("Models loaded successfully from backend.models.__init__.py")