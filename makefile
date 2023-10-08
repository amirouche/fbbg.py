all:
	poetry install
	poetry run python fbbg.py
	python3 -m http.server
