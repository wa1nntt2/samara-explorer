from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Строка подключения к PostgreSQL
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

# Создаем движок
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()