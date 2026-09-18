import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, db_service
from app.core.redis import redis_manager
from app.api.v1.router import api_router
from app.utils.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing MediBot Backend Services, MongoDB & Redis Cache...")
    await connect_to_mongo()
    db_mode = "MongoDB Motor Async" if db_service.is_mongo_connected else "In-Memory Resilient Fallback"
    redis_mode = "Redis Distributed Cache" if redis_manager.is_connected else "In-Memory Resilient Cache"
    logger.info(f"Database Mode: {db_mode}")
    logger.info(f"Cache Mode: {redis_mode}")

    # Warm up AI pipeline in background so first user request is instant
    import asyncio
    from app.services.triage_service import triage_service
    asyncio.create_task(asyncio.to_thread(lambda: getattr(triage_service, "pipeline", None)))

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MediBot Backend Services...")
    await close_mongo_connection()

# Include API Router v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "mode": "mongodb" if db_service.is_mongo_connected else "in_memory_resilient",
            "is_persistent": db_service.is_mongo_connected
        },
        "cache": {
            "mode": "redis" if redis_manager.is_connected else "in_memory_resilient",
            "is_connected": redis_manager.is_connected
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
