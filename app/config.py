from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # База данных
    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 5432
    
    # Приложение
    secret_key: str
    upload_dir: str = "./app/static/uploads"
    
    class Config:
        env_file = ".env"

settings = Settings()