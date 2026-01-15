import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db
from app.config import settings
from geoalchemy2.functions import ST_Point

router = APIRouter(prefix="/places", tags=["places"])

def save_upload_file(upload_file: UploadFile) -> str:
    """Сохраняет загруженный файл и возвращает путь к нему"""
    file_ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return filename

@router.post("/", response_model=schemas.PlaceResponse)
async def create_place(
    title: str = Form(...),
    description: str = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    tags: str = Form(""),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Создание нового места с фото"""
    
    if not photo.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")
    
    photo_filename = save_upload_file(photo)
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
    
    db_place = models.Place(
        title=title,
        description=description,
        lat=lat,
        lon=lon,
        location=ST_Point(lon, lat),
        photo_path=photo_filename,
        user_id=1,
        tags=tag_list
    )
    
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    
    photo_url = f"/static/uploads/{photo_filename}"
    
    return {
        **db_place.__dict__,
        "photo_url": photo_url
    }

@router.get("/", response_model=List[schemas.PlaceResponse])
def get_places(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получение списка мест"""
    places = db.query(models.Place).offset(skip).limit(limit).all()
    
    result = []
    for place in places:
        place_dict = place.__dict__.copy()
        if place.photo_path:
            place_dict["photo_url"] = f"/static/uploads/{place.photo_path}"
        result.append(place_dict)
    
    return result