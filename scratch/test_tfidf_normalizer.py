import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

terms = [
    "Mỏi mắt điều tiết (Asthenopia)", "Đau nhức mắt", "Khô mắt (Dry eye)", "Nhìn mờ / Mắt mờ",
    "Đỏ mắt / Viêm kết mạc", "Chảy nước mắt", "Chấm xuất huyết dưới da", "Đau nhức hốc mắt",
    "Đau nhức khớp", "Phù môi / Phù mạch Angioedema", "Thở rít / Co thắt thanh quản",
    "Mày đay sẩn ngứa cấp tính", "Ngứa dữ dội da niêm mạc", "Sốt cao", "Đau đầu",
    "Đau ngực", "Khó thở", "Đau bụng", "Buồn nôn và nôn", "Tiêu chảy", "Ho khan", "Ho có đờm",
    "Chóng mặt", "Đau nhức cơ toàn thân", "Đau mạn tính kéo dài"
]

t0 = time.time()
vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
embeddings = vectorizer.fit_transform(terms)
t_fit = time.time() - t0
print(f"Fit time: {t_fit*1000:.2f}ms, Shape: {embeddings.shape}")

queries = ["mắt", "mờ mờ", "nhức mắt", "ho khạc", "tức ngực", "ậm ạch", "cộm xốn", "mỏi mắt"]
for q in queries:
    t1 = time.time()
    q_vec = vectorizer.transform([q])
    sims = cosine_similarity(embeddings, q_vec).flatten()
    best_idx = np.argmax(sims)
    best_score = sims[best_idx]
    t_query = time.time() - t1
    print(f"Query: '{q}' -> Best: '{terms[best_idx]}' (Score: {best_score:.4f}, Time: {t_query*1000:.2f}ms)")
