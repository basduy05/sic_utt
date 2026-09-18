.PHONY: dev test build up down clean

dev:
	@echo "Khởi chạy hệ thống ở chế độ phát triển..."
	docker-compose up --build

up:
	docker-compose up -d

down:
	docker-compose down

test:
	@echo "Chạy kiểm thử tự động AI Engine & Backend..."
	python -m pytest apps/ai_engine/tests/
	python -m pytest apps/backend/tests/

seed:
	python scripts/seed_data.py
	python scripts/init_db.py

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
