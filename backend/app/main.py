from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.core.config import settings
from app.api.routes import router

@asynccontextmanager
async def startup_create_tables(app: FastAPI) :
    Base.metadata.create_all(bind=engine)

    yield
app = FastAPI(title=settings.app_name, version=settings.app_version,
              lifespan=startup_create_tables)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
