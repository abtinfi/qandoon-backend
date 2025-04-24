from backend.models.otp import OTP, OTPPurpose
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
from backend.models.user import User

def generate_otp_code(length: int = 5) -> str:
    return ''.join(random.choices(string.digits, k=length))

def create_otp(
    new_user: User,
    purpose: OTPPurpose,
    db: Session,
    expires_minutes: int = 5
) -> OTP:
    code = generate_otp_code()
    otp = OTP(
        id=str(new_user.id),
        email=new_user.email,
        code=code,
        expires_at=datetime.now() + timedelta(minutes=expires_minutes),
        purpose=purpose
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp
