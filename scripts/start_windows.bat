@echo off
if not exist .venv (py -3.12 -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
flask --app wsgi:app bootstrap-db
flask --app wsgi:app seed-assessments
python run.py
