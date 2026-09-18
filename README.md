# Multimodal Medical AI Chatbot (Phiên Bản 3.0.0)

Hệ thống Trợ lý Y Tế AI Đa Phương Thức Doanh Nghiệp (Enterprise-Grade Modular Monorepo) tích hợp Trí tuệ Nhân tạo Đa phương thức: Giọng nói (STT), Bóc tách tài liệu xét nghiệm máu (OCR & Sanity Range Check), PhoBERT Token Classification (Medical NER), Phân tầng bệnh Hybrid Late Fusion (XGBoost + NLP), Cảnh báo Báo Động Đỏ (Red Flag) trong $\le 0.5$s, và Giao diện tương tác thời gian thực (WebSocket Streaming Typewriter & Dynamic Medical Side Dashboard).

---

## 🏗️ Kiến Trúc Hệ Thống (Monorepo Overview)

```
healthcare-multimodal-chatbot/
├── .github/workflows/           # CI/CD Workflows
├── apps/
│   ├── frontend/                # Next.js 14 / Tailwind CSS Chatbot & Side Dashboard
│   ├── backend/                 # FastAPI RESTful & WebSocket Streaming Server
│   └── ai_engine/               # AI Subsystem (STT, OCR, NER, Hybrid Classifier, 5 Colab Notebooks)
├── data/
│   ├── medical_lexicon/         # ICD-10, Từ điển đồng nghĩa, Ngưỡng tham chiếu Lab, Red Flags
│   └── datasets/                # Bộ 50 test cases chuẩn y khoa
├── scripts/                     # Scripts khởi tạo DB và seed tri thức
├── docker/                      # Cấu hình Dockerfiles
├── docker-compose.yml           # Orchestration Local Dev
└── Makefile                     # Lệnh tắt điều khiển
```

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh (Quick Start)

### 1. Yêu cầu tiên quyết
- Docker & Docker Compose
- Node.js $\ge 18$
- Python $\ge 3.10$

### 2. Khởi chạy toàn bộ hệ thống bằng Docker Compose
```bash
# Clone và khởi chạy
make dev
```
- **Frontend Chatbot**: [http://localhost:3000](http://localhost:3000)
- **Admin Portal (Member 1)**: [http://localhost:3000/admin](http://localhost:3000/admin)
- **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Vector Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 3. Chạy Kiểm Thử Tự Động (Automated Testing)
```bash
make test
```

---

## 🔬 Danh Mục 5 Google Colab Notebooks (`apps/ai_engine/notebooks/`)

1. **`01_train_medical_ner_phobert.ipynb`**: Tải `ViMedical_Disease` & `medical-vietnamese-qa`, gán nhãn BIO Tagging và Fine-tune `vinai/phobert-base-v2`.
2. **`02_train_tabular_clinical_xgboost.ipynb`**: Tiền xử lý chỉ số sinh hóa máu + binary triệu chứng, huấn luyện `XGBoost Multi-Class Classifier` trên GPU CUDA.
3. **`03_train_nlp_symptom_classifier.ipynb`**: Huấn luyện mô hình phân loại đa lớp văn bản triệu chứng tiếng Việt ($P_{text}$).
4. **`04_hybrid_late_fusion_and_clarification.ipynb`**: Tối ưu hóa Late Fusion: $P_{final} = \alpha P_{tabular} + (1-\alpha) P_{text}$ và Cây quyết định Entropy Clarification khi $P_{max} < 0.70$.
5. **`05_build_medical_rag_vector_db.ipynb`**: Embedding mã ICD-10 và hướng dẫn Bộ Y tế bằng `BAAI/bge-m3` vào Qdrant Vector Collection.

---

## 🏥 Kịch Bản Nghiệm Thu (Acceptance Scenarios)

1. **Scenario 1 (OCR & Phân tích máu)**: Upload file xét nghiệm máu với $WBC=3.2, PLT=85$ + Sốt cao $\rightarrow$ Tự động cảnh báo Sốt xuất huyết Dengue (A90).
2. **Scenario 2 (Red Flag Khẩn cấp)**: Nhập "Đau ngực dữ dội lan ra vai trái, vã mồ hôi khó thở" $\rightarrow$ Bật Red Flag Emergency Modal trong $\le 0.5$s kèm nút gọi 115.
3. **Scenario 3 (Clarification Loop)**: Nhập triệu chứng mập mờ "đau đầu nhẹ" (độ tin cậy $< 70\%$) $\rightarrow$ Tự động đưa ra 2 câu hỏi làm rõ phân biệt.
4. **Scenario 4 (Ghi âm giọng nói STT)**: Thu âm qua Audio Waveform $\rightarrow$ Faster-Whisper chuyển đổi văn bản tiếng Việt và highlight thực thể.
