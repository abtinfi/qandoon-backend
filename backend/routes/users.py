from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database.config import get_db
from backend.schemas.user import UserCreate, UserLogin, UserUpdate, UserOut
from backend.database.database import create_user, login_user, update_user
from backend.models.user import User
from backend.utils.jwt import verify_access_token


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        

@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        return login_user(db, user.email, user.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
async def edit_user(update: UserUpdate, db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    user = update_user(db, current_user.id, update.model_dump(exclude_unset=True))
    return user

