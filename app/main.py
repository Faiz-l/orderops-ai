from fastapi import FastAPI
from app.database import Base, engine
from app.config import settings
from app.routes import router




# Create DB Tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(router)