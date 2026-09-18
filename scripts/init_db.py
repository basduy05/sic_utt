import os
import json
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")

def init_qdrant_collection():
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name = "medical_knowledge_vi"

    logger.info(f"Initializing Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        logger.info(f"Created collection '{collection_name}' with 1024 dimensions.")
    except Exception as e:
        logger.warning(f"Could not connect to Qdrant server ({e}). Skipping collection creation for now.")

if __name__ == "__main__":
    init_qdrant_collection()
