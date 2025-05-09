from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
from passlib.context import CryptContext

from backend.database.config import get_db
from backend.models.user import User
from backend.schemas.otp import *
from backend.schemas.user import *
from backend.utils.email_service import email_service
from backend.core.security import create_access_token, get_current_user
from backend.database.database import create_user
from backend.core.security import hash_password, verify_password
from redis.client import Redis
from backend.database.redis_config import get_redis
from backend.core.security import generate_otp
import enum


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OTPPurpose(enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    new_user = create_user(db, user_data)

    redis_key = f"otp:{new_user.email}"
    existing_otp_data = redis_client.hgetall(redis_key)
    if existing_otp_data:
        ttl = redis_client.ttl(redis_key)
        if ttl > 0:
            # OTP exists and is not expired
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OTP already exists. Please wait for {ttl} seconds before requesting a new one."
            )
    # Generate OTP
    otp_code = generate_otp()
    expires_in_seconds = 180
    current_time = datetime.now()
    otp_data = {
        "code": otp_code,
        "is_verified": "0",
        "attempts": "0",
        "purpose": OTPPurpose.REGISTRATION.value,
        "created_at": current_time.isoformat(),
    }
    redis_client.hset(redis_key, mapping=otp_data)
    redis_client.expire(redis_key, expires_in_seconds)
    
    await email_service.send_otp_email(user_data.email, otp_code)
    return new_user

@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(otp_request: OTPRequest, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
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
    redis_key =f"otp:{user.email}"
    existing_otp_data = redis_client.hgetall(redis_key)

    if existing_otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An OTP has already been sent. Please wait for it to expire."
        )
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_in_seconds = 180  # 3 minutes
    current_time = datetime.now()
    
    otp_data = {
        "code": otp_code,
        "is_verified": "0",
        "attempts": "0",
        "purpose": otp_request.purpose.value,
        "created_at": current_time.isoformat(),
    }
    
    redis_client.hset(redis_key, mapping=otp_data)
    redis_client.expire(redis_key, expires_in_seconds)

    await email_service.send_otp_email(otp_request.email, otp_code)
    return OTPResponse(
        message="OTP sent successfully",
        expires_in=expires_in_seconds
    )

@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(verify_data: OTPVerifyRequest, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    redis_key = f"otp:{verify_data.email}"
    otp_data = redis_client.hgetall(redis_key)
    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP not found or expired"
        )
    if otp_data["is_verified"] == "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP already verified"
        )
    if otp_data["code"] != verify_data.code:
        redis_client.hincrby(redis_key, "attempts", 1)
        attempts = int(redis_client.hget(redis_key, "attempts"))
        if attempts >= 3:
            ttl = redis_client.ttl(redis_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many attempts. Please request a new OTP after {ttl} seconds"
            )
    # Mark OTP as verified
    if otp_data["code"] == verify_data.code:
        redis_client.hset(redis_key, "is_verified", "1")
        # Update user verification status
        user = db.query(User).filter(User.email == verify_data.email).first()
        if user:
            user.is_verified = True
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    # Create JWT token
    access_token = create_access_token(data={"sub": verify_data.email, "role": "user"})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
    

    

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

    role = "admin" if user.is_admin else "user"
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email, "role": role})
    return TokenResponse(access_token=access_token)

@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    redis_key = f"otp:{request.email}"
    otp_data = redis_client.hgetall(redis_key)
    otp_data = {k.decode(): v.decode() for k, v in otp_data.items()}
    print(otp_data)
    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP not found or expired"
        )
    if otp_data["is_verified"] == "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP already verified"
        )
    if otp_data["code"] != request.code:
        redis_client.hincrby(redis_key, "attempts", 1)
        attempts = int(redis_client.hget(redis_key, "attempts"))
        if attempts >= 3:
            ttl = redis_client.ttl(redis_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many attempts. Please request a new OTP after {ttl} seconds"
            )
    if otp_data["code"] == request.code:
        redis_client.hset(redis_key, "is_verified", "1")
        # Update user password
        user = db.query(User).filter(User.email == request.email).first()
        if user:
            hashed_password = hash_password(request.new_password)
            user.password = hashed_password
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    # Create JWT token
    role = "admin" if user.is_admin else "user"
    access_token = create_access_token(data={"sub": request.email, "role": role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
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