.PHONY: update-env format lint test run shell

# Uppdatera eller skapa conda-miljön från environment.yml
update-env:
	conda env update -f environment.yml

# Formatera kod med Black och isort
format:
	black .
	isort .

# Kör flake8
lint:
	flake8 .

# Kör tester
test:
	pytest --maxfail=1 --disable-warnings --verbose

# Starta tradingboten
run:
	python src/tradingbot.py

# Öppna interaktiv shell
shell:
	conda activate tradingbot_env && ipython
