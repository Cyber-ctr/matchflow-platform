FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin matchflow \
    && mkdir -p instance/uploads \
    && chown -R matchflow:matchflow /app

USER matchflow

EXPOSE 8000

CMD ["gunicorn", "--workers", "3", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--bind", "0.0.0.0:8000", "wsgi:app"]
