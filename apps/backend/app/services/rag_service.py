import hashlib
import logging
from typing import List, Dict, Any, Optional
from ..core.vector_store import vector_store
from ..core.redis import redis_manager
from ..core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self._sync_cache: Dict[str, List[Dict[str, Any]]] = {}

    def retrieve_medical_knowledge(self, query: str, disease_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Truy vấn tri thức y khoa RAG đồng bộ với bộ nhớ đệm (In-memory Cache).
        """
        clean_q = (query or "").strip().lower()
        cache_key = f"rag:{disease_code or 'none'}:{hashlib.md5(clean_q.encode('utf-8')).hexdigest()}"
        if cache_key in self._sync_cache:
            return self._sync_cache[cache_key]
        
        results = vector_store.search_similar(query, disease_code=disease_code)
        self._sync_cache[cache_key] = results
        return results

    async def a_retrieve_medical_knowledge(self, query: str, disease_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Truy vấn tri thức y khoa RAG bất đồng bộ kèm Redis Distributed Cache (TTL cấu hình).
        """
        clean_q = (query or "").strip().lower()
        cache_key = f"rag:{disease_code or 'none'}:{hashlib.md5(clean_q.encode('utf-8')).hexdigest()}"
        
        cached = await redis_manager.get_json(cache_key)
        if cached is not None:
            return cached
            
        results = vector_store.search_similar(query, disease_code=disease_code)
        await redis_manager.set_json(cache_key, results, ex=settings.CACHE_TTL_RAG)
        self._sync_cache[cache_key] = results
        return results

rag_service = RAGService()
