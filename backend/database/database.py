from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate
from backend.core.security import hash_password, verify_password
from fastapi import HTTPException, status

def create_user(db: Session, user_data: UserCreate):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email.lower(),
        name=user_data.name,
        password=hashed_pw,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Created user with ID: {new_user.id}")
    return new_user

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")
    
    return user

def update_user(db: Session, user_id: int, update_data: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    if "email" in update_data:
        user.email = update_data["email"]
    if "password" in update_data:
        user.hashed_password = hash_password(update_data["password"])
    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]
    
    db.commit()
    db.refresh(user)
    return user


# end of the line


