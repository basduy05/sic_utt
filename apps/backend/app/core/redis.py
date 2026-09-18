import json
import time
import logging
from typing import Optional, Any, Dict, Tuple
from .config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Async Redis Manager hỗ trợ:
    - Async Redis client (aioredis) với connection pooling.
    - Resilient In-Memory Fallback Cache có hỗ trợ TTL (Time To Live).
    - Tiện ích get/set dữ liệu JSON tự động serialize/deserialize.
    """
    def __init__(self):
        self.redis = None
        self._memory_cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._tested_connection = False
        self._is_online = False
        self._init_redis()

    def _init_redis(self):
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.05)
            sock.connect(("127.0.0.1", 6379))
            sock.close()
            is_open = True
        except Exception:
            is_open = False

        if not is_open:
            logger.info("Redis server offline. Operating in resilient In-Memory cache mode.")
            self.redis = None
            self._is_online = False
            return

        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5
            )
            logger.info("Initialized Redis client instance.")
        except Exception as e:
            logger.warning(f"Failed to create Redis client ({e}). Operating in resilient In-Memory cache mode.")
            self.redis = None

    async def is_connected(self) -> bool:
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            self._is_online = True
            return True
        except Exception:
            self._is_online = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """Lấy giá trị string theo key."""
        if self.redis:
            try:
                val = await self.redis.get(key)
                return val
            except Exception as e:
                logger.debug(f"Redis get failed ({e}), using memory fallback.")

        # In-memory fallback with TTL check
        item = self._memory_cache.get(key)
        if item:
            val, expire_at = item
            if expire_at is not None and time.time() > expire_at:
                del self._memory_cache[key]
                return None
            return str(val) if not isinstance(val, str) else val
        return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Lưu giá trị string với TTL (giây)."""
        saved = False
        if self.redis:
            try:
                await self.redis.set(key, value, ex=ex)
                saved = True
            except Exception as e:
                logger.debug(f"Redis set failed ({e}), using memory fallback.")

        # Always update memory fallback for high resilience
        expire_at = (time.time() + ex) if ex else None
        self._memory_cache[key] = (value, expire_at)
        return True

    async def get_json(self, key: str) -> Optional[Any]:
        """Lấy dữ liệu JSON và deserialize thành Python object."""
        if self.redis:
            try:
                raw = await self.redis.get(key)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.debug(f"Redis get_json failed ({e}), using memory fallback.")

        # In-memory fallback
        item = self._memory_cache.get(key)
        if item:
            val, expire_at = item
            if expire_at is not None and time.time() > expire_at:
                del self._memory_cache[key]
                return None
            return val
        return None

    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Serialize Python object thành JSON và lưu vào cache kèm TTL (giây)."""
        expire_at = (time.time() + ex) if ex else None
        self._memory_cache[key] = (value, expire_at)

        if self.redis:
            try:
                dumped = json.dumps(value, ensure_ascii=False)
                await self.redis.set(key, dumped, ex=ex)
                return True
            except Exception as e:
                logger.debug(f"Redis set_json failed ({e}), memory fallback preserved.")

        return True

    async def delete(self, key: str) -> bool:
        """Xóa key khỏi cache."""
        deleted = False
        if self.redis:
            try:
                await self.redis.delete(key)
                deleted = True
            except Exception as e:
                logger.debug(f"Redis delete failed ({e}).")

        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True
        return deleted

    async def exists(self, key: str) -> bool:
        """Kiểm tra sự tồn tại của key trong cache."""
        if self.redis:
            try:
                return bool(await self.redis.exists(key))
            except Exception:
                pass
        item = self._memory_cache.get(key)
        if item:
            _, expire_at = item
            if expire_at is not None and time.time() > expire_at:
                del self._memory_cache[key]
                return False
            return True
        return False

    async def close(self):
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass

redis_manager = RedisManager()
