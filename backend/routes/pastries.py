from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from pathlib import Path
from datetime import datetime

from backend.database.config import get_db
from backend.models.pastry import Pastry
from backend.schemas.pastry import PastryCreate, PastryUpdate, PastryResponse
from backend.core.security import get_current_user

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/pastries")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

async def save_upload_file(upload_file: UploadFile) -> str:
    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Read file in chunks to check size
    while chunk := await upload_file.read(chunk_size):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
    
    # Reset file pointer
    await upload_file.seek(0)
    
    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{upload_file.filename}_{datetime.now().timestamp()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return str(file_path)

@router.post("/", response_model=PastryResponse, status_code=status.HTTP_201_CREATED)
async def create_pastry(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create pastries"
        )
    
    # Save uploaded image
    image_url = await save_upload_file(image)
    
    # Create pastry
    pastry_data = {
        "name": name,
        "description": description,
        "image_url": image_url,
        "price": price,
        "stock": stock
    }
    
    db_pastry = Pastry(**pastry_data)
    db.add(db_pastry)
    db.commit()
    db.refresh(db_pastry)
    return db_pastry

@router.get("/", response_model=List[PastryResponse])
async def get_pastries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    pastries = db.query(Pastry).offset(skip).limit(limit).all()
    return pastries

@router.get("/{pastry_id}", response_model=PastryResponse)
async def get_pastry(
    pastry_id: int,
    db: Session = Depends(get_db)
):
    pastry = db.query(Pastry).filter(Pastry.id == pastry_id).first()
    if not pastry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pastry not found"
        )
    return pastry

@router.put("/{pastry_id}", response_model=PastryResponse)
async def update_pastry(
    pastry_id: int,
    name: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    stock: int = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update pastries"
        )
    
    db_pastry = db.query(Pastry).filter(Pastry.id == pastry_id).first()
    if not db_pastry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pastry not found"
        )
    
    # Update fields if provided
    if name is not None:
        db_pastry.name = name
    if description is not None:
        db_pastry.description = description
    if price is not None:
        db_pastry.price = price
    if stock is not None:
        db_pastry.stock = stock
    
    # Handle image upload if provided
    if image is not None:
        # Delete old image if exists
        if db_pastry.image_url and os.path.exists(db_pastry.image_url):
            os.remove(db_pastry.image_url)
        
        # Save new image
        image_url = await save_upload_file(image)
        db_pastry.image_url = image_url
    
    db.commit()
    db.refresh(db_pastry)
    return db_pastry

@router.delete("/{pastry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pastry(
    pastry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete pastries"
        )
    
    db_pastry = db.query(Pastry).filter(Pastry.id == pastry_id).first()
    if not db_pastry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pastry not found"
        )
    
    # Delete image file if exists
    if db_pastry.image_url and os.path.exists(db_pastry.image_url):
        os.remove(db_pastry.image_url)
    
    db.delete(db_pastry)
    db.commit()
    return status.HTTP_200_OK