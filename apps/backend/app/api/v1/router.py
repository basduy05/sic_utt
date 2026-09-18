from fastapi import APIRouter
from .endpoints import auth, chat, upload, medical, admin, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(medical.router, prefix="/medical", tags=["Medical AI & Triage"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & QA"])
api_router.include_router(websocket.router, tags=["WebSocket Realtime"])
