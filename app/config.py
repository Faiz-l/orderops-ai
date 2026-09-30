from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OrderOps AI"
    DATABASE_URL: str = "sqlite:///./orderops.db"
    GEMINI_API_KEY: str = ""
    FRAUD_THRESHOLD: float = 0.75

    class Config:
        env_file = ".env"

settings = Settings()