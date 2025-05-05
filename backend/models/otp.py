from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum
from sqlalchemy.sql import func
from backend.database.config import Base
from datetime import datetime, timezone
import enum

class OTPPurpose(enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"

class OTP(Base):
    __tablename__ = "otps"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    code = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    attempts = Column(Integer, default=0)
    purpose = Column(Enum(OTPPurpose), nullable=False)

    def is_expired(self):
        # Make sure both datetimes are timezone-aware
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        return now > expires_at

    def increment_attempts(self):
        self.attempts += 1 