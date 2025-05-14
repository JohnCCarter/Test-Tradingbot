install:
	conda env create -f environment.yml

test:
	pytest tests/

lint:
	pre-commit run --all-files