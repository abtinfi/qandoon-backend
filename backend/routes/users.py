# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# from backend.database.config import get_db
# from backend.schemas.user import UserCreate, UserLogin, UserUpdate, UserOut
# from backend.database.database import create_user, login_user, update_user
# from backend.models.user import User
# from backend.utils.jwt import verify_access_token


# router = APIRouter()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     payload = verify_access_token(token)
#     user = db.query(User).filter(User.id == payload["user_id"]).first()
#     if user is None:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     return user

# @router.post("/register", response_model=UserOut)
# async def register(user_data: UserCreate, db: Session = Depends(get_db)):
#     try:
#         user = create_user(db, user_data)
#         return user
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
        

# @router.post("/login")
# async def login(user: UserLogin, db: Session = Depends(get_db)):
#     try:
#         return login_user(db, user.email, user.password)
#     except ValueError as e:
#         raise HTTPException(status_code=401, detail=str(e))

# @router.get("/me", response_model=UserOut)
# async def get_me(current_user: UserOut = Depends(get_current_user)):
#     return current_user

# @router.put("/me", response_model=UserOut)
# async def edit_user(update: UserUpdate, db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
#     user = update_user(db, current_user.id, update.model_dump(exclude_unset=True))
#     return user

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import random
import string
from slowapi import Limiter
from slowapi.util import get_remote_address
from passlib.context import CryptContext

from backend.database.config import get_db
from backend.models.user import User
from backend.models.otp import OTP, OTPPurpose
from backend.schemas.otp import *
from backend.schemas.user import *
from backend.utils.email_service import email_service
from backend.core.security import create_access_token, get_current_user
from backend.database.database import create_user
from backend.database.otp import create_otp
from backend.utils.hashpass import hash_password, verify_password


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
limiter = Limiter(key_func=get_remote_address)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=5))

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    new_user = create_user(db, user_data)
    otp = create_otp(new_user=new_user, db=db, purpose=OTPPurpose.REGISTRATION)
    await email_service.send_otp_email(user_data.email, otp.code)
    return new_user

@router.post("/request-otp", response_model=OTPResponse)
@limiter.limit("3/minute")
async def request_otp(request: Request, otp_request: OTPRequest, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == otp_request.email).first() #TODO: add user finder query
    
    # Validate purpose
    if otp_request.purpose == OTPPurpose.REGISTRATION:
        if user and user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified"
            )
    elif otp_request.purpose == OTPPurpose.PASSWORD_RESET:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified. Please verify your email first."
            )
    
    # Check if there's an existing OTP
    existing_otp = db.query(OTP).filter(OTP.email == otp_request.email).first()
    
    if existing_otp and not existing_otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting a new OTP"
        )

    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)
    
    if existing_otp:
        existing_otp.code = otp_code
        existing_otp.expires_at = expires_at
        existing_otp.is_verified = False
        existing_otp.attempts = 0
        existing_otp.purpose = otp_request.purpose
    else:
        new_otp = OTP(
            id=str(random.randint(1000, 9999)),
            email=otp_request.email,
            code=otp_code,
            expires_at=expires_at,
            purpose=otp_request.purpose
        )
        db.add(new_otp)
    
    db.commit()
    
    # Send email
    await email_service.send_otp_email(otp_request.email, otp_code)
    
    return OTPResponse(
        message="OTP sent successfully",
        expires_in=300  # 5 minutes in seconds
    )

@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(verify_data: OTPVerifyRequest, db: Session = Depends(get_db)):
    email = verify_data.email
    code = verify_data.code
    # Verify OTP
    otp = db.query(OTP).filter(OTP.email == email).first()
    if not otp or otp.code != code or otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Update user verification status
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_verified = True
    db.commit()

    # Generate JWT token
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if user:
    # Check password (in production, use proper password hashing)
        if not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token)

@router.post("/reset-password", response_model=OTPResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Verify OTP first
    otp = db.query(OTP).filter(OTP.email == request.email).first()
    
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP not found"
        )
    
    if otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
    
    if otp.attempts >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Please request a new OTP"
        )
    
    if otp.code != request.code:
        otp.increment_attempts()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Find user and update password
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the new password
    hashed_password = hash_password(request.new_password)
    user.password = hashed_password
    
    # Mark OTP as verified
    otp.is_verified = True
    
    db.commit()
    
    return OTPResponse(
        message="Password reset successfully",
        expires_in=0
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_user).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user