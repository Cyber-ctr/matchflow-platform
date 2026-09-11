import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, url_for
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv(override=False)

from .config import Config
from .extensions import csrf, db, limiter, login_manager, migrate
from .models import Notification, User


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or Config)
    app.config.setdefault('UPLOAD_FOLDER', str(Path(app.root_path).parent / 'instance' / 'uploads'))
    if os.getenv('FLASK_ENV') == 'production' and app.config['SECRET_KEY'] == 'change-me-in-production':
        raise RuntimeError('SECRET_KEY must be set to a strong secret in production.')
    from .cli import register_commands
    register_commands(app)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if os.getenv('TRUST_PROXY', '0') == '1':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.template_filter('fromjson')
    def fromjson(value):
        import json
        return json.loads(value)

    @app.template_filter('money')
    def money(value):
        if value is None:
            return 'Negotiable'
        return f'{float(value):,.0f} FCFA'

    @app.template_filter('dt')
    def dt(value):
        return value.strftime('%d %b %Y') if value else '—'

    @app.context_processor
    def inject_globals():
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(
                user_id=current_user.id, read_at=None,
            ).count()
        return {'now': datetime.utcnow(), 'unread_notifications': unread}

    @app.after_request
    def security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; img-src 'self' data:; font-src 'self'; "
            "connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'",
        )
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response

    @app.errorhandler(403)
    def forbidden(_):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(_):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        from flask import render_template
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def too_large(_):
        flash('The uploaded file is too large. Maximum allowed size is 5 MB.', 'error')
        return redirect(url_for('main.home'))

    from .main.routes import bp as main_bp
    from .auth.routes import bp as auth_bp
    from .auth.reset_routes import bp as reset_bp
    from .auth.verify_routes import bp as verify_bp
    from .talent.routes import bp as talent_bp
    from .employer.routes import bp as employer_bp
    from .admin.routes import bp as admin_bp
    from .admin.job_routes import bp as admin_jobs_bp
    from .api.routes import bp as api_bp
    from .main.extra import bp as messaging_bp
    from .talent.extra import bp as talent_extra_bp
    from .employer.extra import bp as employer_extra_bp
    from .talent.assessment_routes import bp as assessment_bp
    from .talent.cv_routes import bp as cv_bp
    from .employer.apprenticeship_routes import bp as employer_apprenticeship_bp
    from .employer.billing_routes import bp as billing_bp

    app.add_url_rule('/dashboard', 'dashboard', __import__('app.routes', fromlist=['dashboard']).dashboard)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(reset_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(talent_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_jobs_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(talent_extra_bp)
    app.register_blueprint(employer_extra_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(employer_apprenticeship_bp)
    app.register_blueprint(billing_bp)

    return app
