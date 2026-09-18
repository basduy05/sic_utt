import os
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SymptomTextEncoder:
    """
    Mã hóa văn bản triệu chứng y tế thành vector biểu diễn (Dense Embeddings).
    Hỗ trợ BAAI/bge-m3 hoặc PhoBERT embedding với lightweight fallback.
    """

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        # Initialized lazily to avoid startup blockage

    def _init_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"SentenceTransformer '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using lightweight hash vectorizer.")
            self.model = None

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Nhận vào danh sách chuỗi, trả về numpy ndarray shape (N, D).
        """
        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, normalize_embeddings=True)
                return np.array(embeddings)
            except Exception as e:
                logger.error(f"Error encoding with SentenceTransformer: {e}")

        # Lightweight fallback deterministic representation with stopword removal
        stopwords = {"tôi", "bị", "thấy", "người", "hơi", "và", "ở", "có", "rất", "lắm", "quá", "hôm", "nay", "được", "một", "cho", "với", "như", "là", "đang"}
        embeddings = []
        dim = 256
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            words = [w for w in text.lower().split() if w not in stopwords and len(w) > 1]
            for word in words:
                h = abs(hash(word)) % dim
                vec[h] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        return np.array(embeddings)
