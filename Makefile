.PHONY: help install setup demo full clean test lint format docker-up docker-down

help:
	@echo "GeoReach - Makefile Commands"
	@echo "============================"
	@echo "install      - Install Python dependencies"
	@echo "setup        - Set up database and environment"
	@echo "demo         - Run full pipeline with subset data (QUICK)"
	@echo "full         - Run full pipeline with complete data"
	@echo "clean        - Clean generated data and outputs"
	@echo "test         - Run tests"
	@echo "lint         - Run linters (ruff, mypy)"
	@echo "format       - Format code (black, ruff)"
	@echo "docker-up    - Start Docker services"
	@echo "docker-down  - Stop Docker services"
	@echo "docker-demo  - Run demo in Docker (ONE COMMAND)"

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

setup:
	cp .env.example .env
	mkdir -p data/raw data/processed data/outputs data/subset
	docker-compose up -d postgis
	@echo "Waiting for PostGIS to be ready..."
	@sleep 5

demo: setup
	@echo "Running GeoReach demo pipeline..."
	georeach pipeline --subset
	@echo "Demo complete! Open http://localhost:8080 to view the map"

full: setup
	@echo "Running full GeoReach pipeline..."
	georeach pipeline
	@echo "Full pipeline complete!"

clean:
	rm -rf data/raw/* data/processed/* data/outputs/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

test:
	pytest tests/ -v --cov=georeach --cov-report=term-missing

lint:
	ruff check georeach/ tests/
	mypy georeach/

format:
	black georeach/ tests/
	ruff check --fix georeach/ tests/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-demo:
	@echo "Starting GeoReach in Docker..."
	docker-compose up --build
	@echo "Demo complete! Open http://localhost:8080 to view the map"

docker-clean:
	docker-compose down -v
	docker system prune -f
