from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, func, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
import uuid
import hashlib

# Настройки
DB_URL = "postgresql://explorer:secretpassword123@localhost:5432/samara_db"
UPLOAD_DIR = "app/static/uploads"
TEMPLATES_DIR = "app/templates"

# Создаем папки если их нет
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# База данных
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель пользователя (упрощенная)
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(64), nullable=False)  # SHA256 хеш
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Модель места
class PlaceDB(Base):
    __tablename__ = "places"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    photo_path = Column(String(500))
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Pydantic схемы
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class PlaceBase(BaseModel):
    title: str
    description: Optional[str] = None
    lat: float
    lon: float

class PlaceResponse(PlaceBase):
    id: int
    photo_url: Optional[str] = None
    user_id: int
    user_username: str
    created_at: datetime

# Вспомогательные функции
def hash_password(password: str) -> str:
    """Хеширует пароль с помощью SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    return hash_password(password) == hashed_password

# Простая система сессий (в памяти, для демо)
user_sessions = {}  # token -> user_id

# FastAPI приложение
app = FastAPI(title="Samara Explorer API", version="1.2.0")

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def save_upload_file(upload_file: UploadFile) -> str:
    """Сохраняет файл и возвращает имя файла"""
    file_ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return filename

def get_current_user(request: Request):
    """Получает текущего пользователя из cookies"""
    token = request.cookies.get("session_token")
    if not token or token not in user_sessions:
        return None
    user_id = user_sessions[token]
    
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        return user
    finally:
        db.close()

# Веб-интерфейс
@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Главная страница с веб-интерфейсом"""
    current_user = get_current_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})

# Аутентификация API
@app.post("/api/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...)
):
    """Регистрация нового пользователя"""
    db = SessionLocal()
    try:
        # Проверяем, существует ли пользователь
        existing_user = db.query(UserDB).filter(UserDB.username == username).first()
        if existing_user:
            raise HTTPException(400, "Пользователь с таким именем уже существует")
        
        # Создаем нового пользователя
        password_hash = hash_password(password)
        db_user = UserDB(
            username=username,
            password_hash=password_hash
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Создаем сессию
        session_token = str(uuid.uuid4())
        user_sessions[session_token] = db_user.id
        
        return {
            "message": "Регистрация успешна",
            "username": db_user.username,
            "user_id": db_user.id,
            "session_token": session_token
        }
    finally:
        db.close()

@app.post("/api/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...)
):
    """Вход пользователя"""
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            raise HTTPException(400, "Неверное имя пользователя или пароль")
        
        if not verify_password(password, user.password_hash):
            raise HTTPException(400, "Неверное имя пользователя или пароль")
        
        # Создаем сессию
        session_token = str(uuid.uuid4())
        user_sessions[session_token] = user.id
        
        return {
            "message": "Вход выполнен успешно",
            "username": user.username,
            "user_id": user.id,
            "session_token": session_token
        }
    finally:
        db.close()

@app.post("/api/logout")
async def logout_user(request: Request):
    """Выход пользователя"""
    token = request.cookies.get("session_token")
    if token in user_sessions:
        del user_sessions[token]
    
    return {"message": "Выход выполнен успешно"}

@app.get("/api/users/me")
async def get_current_user_info(request: Request):
    """Получение информации о текущем пользователе"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Не авторизован")
    
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat()
    }

# API эндпоинты
@app.post("/api/places/")
async def create_place(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    photo: UploadFile = File(...)
):
    """Создание нового места (требуется аутентификация)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    
    if not photo.content_type.startswith('image/'):
        raise HTTPException(400, "Файл должен быть изображением")
    
    db = SessionLocal()
    try:
        photo_filename = save_upload_file(photo)
        
        db_place = PlaceDB(
            title=title,
            description=description,
            lat=lat,
            lon=lon,
            photo_path=photo_filename,
            user_id=user.id
        )
        
        db.add(db_place)
        db.commit()
        db.refresh(db_place)
        
        return {
            "id": db_place.id,
            "title": db_place.title,
            "description": db_place.description,
            "lat": db_place.lat,
            "lon": db_place.lon,
            "photo_url": f"/static/{photo_filename}",
            "user_id": db_place.user_id,
            "user_username": user.username,
            "created_at": db_place.created_at.isoformat()
        }
    finally:
        db.close()

@app.get("/api/places/", response_model=List[PlaceResponse])
def get_places(skip: int = 0, limit: int = 100):
    """Получение списка мест"""
    db = SessionLocal()
    try:
        places = db.query(PlaceDB).order_by(PlaceDB.created_at.desc()).offset(skip).limit(limit).all()
        
        # Получаем информацию о пользователях
        user_ids = [place.user_id for place in places]
        users = {user.id: user for user in db.query(UserDB).filter(UserDB.id.in_(user_ids)).all()}
        
        result = []
        for place in places:
            user = users.get(place.user_id)
            result.append({
                "id": place.id,
                "title": place.title,
                "description": place.description,
                "lat": place.lat,
                "lon": place.lon,
                "photo_url": f"/static/{place.photo_path}" if place.photo_path else None,
                "user_id": place.user_id,
                "user_username": user.username if user else "Неизвестно",
                "created_at": place.created_at
            })
        return result
    finally:
        db.close()

@app.get("/api/places/bbox/", response_model=List[PlaceResponse])
def get_places_by_bbox(
    min_lat: float = Query(..., description="Минимальная широта (южная граница)"),
    max_lat: float = Query(..., description="Максимальная широта (северная граница)"),
    min_lon: float = Query(..., description="Минимальная долгота (западная граница)"),
    max_lon: float = Query(..., description="Максимальная долгота (восточная граница)")
):
    """Получение мест в заданной прямоугольной области"""
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise HTTPException(400, "Широта должна быть в диапазоне [-90, 90]")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise HTTPException(400, "Долгота должна быть в диапазоне [-180, 180]")
    
    db = SessionLocal()
    try:
        places = db.query(PlaceDB).filter(
            and_(
                PlaceDB.lat >= min_lat,
                PlaceDB.lat <= max_lat,
                PlaceDB.lon >= min_lon,
                PlaceDB.lon <= max_lon
            )
        ).all()
        
        # Получаем информацию о пользователях
        user_ids = [place.user_id for place in places]
        users = {user.id: user for user in db.query(UserDB).filter(UserDB.id.in_(user_ids)).all()}
        
        result = []
        for place in places:
            user = users.get(place.user_id)
            result.append({
                "id": place.id,
                "title": place.title,
                "description": place.description,
                "lat": place.lat,
                "lon": place.lon,
                "photo_url": f"/static/{place.photo_path}" if place.photo_path else None,
                "user_id": place.user_id,
                "user_username": user.username if user else "Неизвестно",
                "created_at": place.created_at
            })
        return result
    finally:
        db.close()

@app.get("/api/users/{user_id}/places", response_model=List[PlaceResponse])
def get_user_places(user_id: int):
    """Получение мест конкретного пользователя"""
    db = SessionLocal()
    try:
        places = db.query(PlaceDB).filter(PlaceDB.user_id == user_id).order_by(PlaceDB.created_at.desc()).all()
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        
        result = []
        for place in places:
            result.append({
                "id": place.id,
                "title": place.title,
                "description": place.description,
                "lat": place.lat,
                "lon": place.lon,
                "photo_url": f"/static/{place.photo_path}" if place.photo_path else None,
                "user_id": place.user_id,
                "user_username": user.username if user else "Неизвестно",
                "created_at": place.created_at
            })
        return result
    finally:
        db.close()

@app.get("/health")
async def health():
    """Проверка здоровья приложения"""
    db = SessionLocal()
    try:
        # Проверяем подключение к БД
        db.execute("SELECT 1")
        db_status = "connected"
        # Проверяем количество пользователей и мест
        users_count = db.query(UserDB).count()
        places_count = db.query(PlaceDB).count()
        active_sessions = len(user_sessions)
    except:
        db_status = "disconnected"
        users_count = 0
        places_count = 0
        active_sessions = 0
    finally:
        db.close()
    
    return {
        "status": "healthy",
        "database": db_status,
        "users_count": users_count,
        "places_count": places_count,
        "active_sessions": active_sessions,
        "version": "1.2.0"
    }
