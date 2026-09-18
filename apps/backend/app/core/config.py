import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal Medical AI Chatbot Backend"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "medical-ai-sec-9a8f23b7e6d1c4a0f8e5b2d7c1a9e3f5b8c2d6e4")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "medical-ai-ref-7c1a9e3f5b8c2d6e49a8f23b7e6d1c4a0f8e5b2d")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days
    
    # Cache TTLs (in seconds)
    CACHE_TTL_TRIAGE: int = int(os.getenv("CACHE_TTL_TRIAGE", "3600"))
    CACHE_TTL_RAG: int = int(os.getenv("CACHE_TTL_RAG", "1800"))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    # LLM Providers (Hybrid, Local Ollama/vLLM, or Google Gemini)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "hybrid")  # hybrid | local | gemini | rule_based
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
    LOCAL_LLM_TYPE: str = os.getenv("LOCAL_LLM_TYPE", "ollama")  # ollama | openai
    LOCAL_LLM_TIMEOUT: float = float(os.getenv("LOCAL_LLM_TIMEOUT", "30.0"))
    
    # Database (MongoDB)
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = "medical_chatbot_db"
    
    # Vector DB (Qdrant) & Dense Embeddings
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "medical_knowledge_vi"
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Storage (S3 / MinIO)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = "medical-uploads"
    MINIO_SECURE: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
