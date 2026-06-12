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

create-admin:
	docker-compose exec app uv run python -m app.cli.manage create-admin $(USERNAME) $(PASSWORD)

grant-role:
	docker-compose exec app uv run python -m app.cli.manage grant-role $(USERNAME) $(ROLE)
