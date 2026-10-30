import json
import logging
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from flask import g, has_request_context, request


def _safe_path(path):
    for prefix in ('/auth/reset-password/', '/auth/verify/'):
        if path.startswith(prefix):
            return f'{prefix}[redacted]'
    return path


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if has_request_context():
            entry['request_id'] = getattr(g, 'request_id', None)
            entry['method'] = request.method
            entry['path'] = _safe_path(request.path)
        if hasattr(record, 'http_status'):
            entry['http_status'] = record.http_status
        if hasattr(record, 'duration_ms'):
            entry['duration_ms'] = record.duration_ms
        if record.exc_info:
            entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=True)


def configure_observability(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.propagate = False

    sentry_dsn = app.config.get('SENTRY_DSN')
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        def scrub_event(event, hint):
            request_data = event.get('request')
            if request_data:
                request_data.pop('data', None)
                request_data.pop('cookies', None)
                request_data.pop('headers', None)
                request_data.pop('query_string', None)
                url = request_data.get('url')
                if url:
                    parts = urlsplit(url)
                    request_data['url'] = urlunsplit((
                        parts.scheme, parts.netloc, _safe_path(parts.path), '', '',
                    ))
            if has_request_context():
                event.setdefault('tags', {})['request_id'] = getattr(g, 'request_id', '')
            return event

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            send_default_pii=False,
            traces_sample_rate=app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0),
            before_send=scrub_event,
        )
