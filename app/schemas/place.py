from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class PlaceBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tags: List[str] = []

class PlaceCreate(PlaceBase):
    user_id: int = 1

class PlaceResponse(PlaceBase):
    id: int
    photo_url: Optional[str] = None
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True