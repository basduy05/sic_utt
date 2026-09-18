#!/bin/bash
set -e

echo "=== Cài đặt môi trường phát triển Multimodal Medical AI Chatbot ==="

# 1. AI Engine setup
echo "Cài đặt phụ thuộc AI Engine..."
cd apps/ai_engine
pip install -r requirements.txt
cd ../..

# 2. Backend setup
echo "Cài đặt phụ thuộc Backend FastAPI..."
cd apps/backend
pip install -r requirements.txt
cd ../..

# 3. Frontend setup
echo "Cài đặt phụ thuộc Frontend Next.js..."
cd apps/frontend
npm install
cd ../..

echo "Khởi tạo dữ liệu mẫu..."
python scripts/seed_data.py

echo "=== Cài đặt hoàn tất! Sử dụng 'make dev' để khởi chạy toàn bộ hệ thống. ==="
