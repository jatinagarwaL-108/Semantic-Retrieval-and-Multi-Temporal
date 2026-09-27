"""
Backend Configuration Module
"""

import os


class Settings:
    PROJECT_NAME: str = "MiraeNova Satellite Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    DATA_RAW_DIR: str = os.getenv("DATA_RAW_DIR", "data/raw")
    DATA_PROCESSED_DIR: str = os.getenv("DATA_PROCESSED_DIR", "data/processed")
    DATA_COMPOSITES_DIR: str = os.getenv("DATA_COMPOSITES_DIR", "data/composites")
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/miraenova.db")
    
    TITILER_ENDPOINT: str = os.getenv("TITILER_ENDPOINT", "http://localhost:8000/api/tiles")


settings = Settings()
