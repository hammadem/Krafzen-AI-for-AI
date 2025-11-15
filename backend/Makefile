.PHONY: run test db-setup format lint install

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest tests/ -v --cov=app/ --cov-report=html

db-setup:
	./scripts/setup_supabase.sh

format:
	black . && isort .

lint:
	ruff check .
