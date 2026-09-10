install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

bootstrap:
	flask --app wsgi:app bootstrap-db
	flask --app wsgi:app seed-assessments

seed:
	flask --app wsgi:app seed-demo

run:
	python run.py

test:
	pytest -q

lint-py:
	python -m compileall -q app tests run.py wsgi.py
