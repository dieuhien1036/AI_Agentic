.PHONY: setup lint type test test-integration run migrate-dry-run clean

setup:
	uv sync

lint:
	uv run ruff check .

type:
	uv run mypy app

test:
	uv run pytest -q

test-integration:
	uv run pytest tests/integration -q

run:
	uv run uvicorn app.main:app --reload --port 8000

migrate-dry-run:
	@echo "Dry-run only. Real migrations are applied via the deploy pipeline."
	@cat migrations/*.sql | head -50

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
