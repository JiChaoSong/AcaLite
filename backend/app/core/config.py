from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "AcaLite API"
    app_version: str = "0.1.0"
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://acalite:acalite@postgres:5432/acalite"
    )
    storage_path: str = os.getenv("STORAGE_PATH", "/data/documents")

    ai_provider: str = os.getenv("AI_PROVIDER", "heuristic")
    ai_base_url: str = os.getenv("AI_BASE_URL", "")
    ai_model: str = os.getenv("AI_MODEL", "")
    ai_api_key: str = os.getenv("AI_API_KEY", "")


settings = Settings()
