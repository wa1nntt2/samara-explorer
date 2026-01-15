from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class Place(Base):
    __tablename__ = "places"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    
    # PostGIS geometry field
    location = Column(Geometry('POINT', srid=4326))
    
    photo_path = Column(String(500))
    user_id = Column(Integer, nullable=False, default=1)
    tags = Column(JSONB, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())