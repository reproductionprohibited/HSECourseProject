.PHONY: restart lint format default test

restart:
	docker-compose down -v && docker-compose build && docker-compose up -d

lint:
	uv run ruff check

format:
	uv run ruff check --fix && uv run ruff format

default:
	make lint && make format && make lint

test:
	docker-compose exec app uv run pytest --cov=app --cov-report=term-missing

