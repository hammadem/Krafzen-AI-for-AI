.PHONY: run test db-setup format lint install

install:
	pip install -r requirements.txt

run:
	@echo "Starting server..."
	@if [ -d "venv" ]; then \
		. venv/bin/activate && uvicorn app.main:app --reload; \
	else \
		python3 -m uvicorn app.main:app --reload; \
	fi

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=app/ --cov-report=html

db-setup:
	./scripts/setup_supabase.sh

format:
	black . && isort .

lint:
	ruff check .
