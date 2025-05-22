lint:
	ruff check src/
	ruff check tests/

test:
	pytest 