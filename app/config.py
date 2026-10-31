import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def database_uri():
    url = os.getenv('DATABASE_URL', '').strip()
    if not url:
        return f"sqlite:///{BASE_DIR / 'matchflow.db'}"
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_MB', '5')) * 1024 * 1024
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'
    TRUSTED_HOSTS = [h.strip() for h in os.getenv('TRUSTED_HOSTS', '').split(',') if h.strip()] or None
    RATELIMIT_DEFAULT = '200 per day;50 per hour'
    RATELIMIT_STORAGE_URI = (
        os.getenv('RATELIMIT_STORAGE_URI')
        or os.getenv('REDIS_URL')
        or 'memory://'
    )
    APP_NAME = 'MatchFlow'
    CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'hello@matchflow.cm')
    UPLOAD_FOLDER = str(BASE_DIR / 'instance' / 'uploads')
    OBJECT_STORAGE_BUCKET = os.getenv('OBJECT_STORAGE_BUCKET', '')
    OBJECT_STORAGE_ENDPOINT_URL = os.getenv('OBJECT_STORAGE_ENDPOINT_URL', '')
    OBJECT_STORAGE_REGION = os.getenv('OBJECT_STORAGE_REGION', 'auto')
    OBJECT_STORAGE_PREFIX = os.getenv('OBJECT_STORAGE_PREFIX', 'matchflow')
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
