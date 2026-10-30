from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db
from app.models import User

bp = Blueprint('password_reset', __name__, url_prefix='/auth')


def serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='matchflow-password-reset')


@bp.post('/forgot-password')
def request_reset():
    email = request.form.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first()
    if user:
        token = serializer().dumps(user.email)
        reset_url = url_for('password_reset.reset_password', token=token, _external=True)
        from app.services.email import send_email
        sent = send_email(
            email,
            'Reset your MatchFlow password',
            f'Use this link within 60 minutes to reset your MatchFlow password:\n\n{reset_url}',
        )
        from flask import current_app
        if not sent:
            if current_app.config.get('TESTING') or current_app.debug:
                current_app.logger.info('SMTP is not configured; password reset email was not sent')
            else:
                current_app.logger.warning('Password reset email could not be delivered')
    flash('If an account exists for that email, a reset link has been generated.', 'success')
    return redirect(url_for('password_reset.forgot_password'))


@bp.get('/forgot-password')
def forgot_password():
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer().loads(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        flash('The reset link is invalid or expired.', 'error')
        return redirect(url_for('password_reset.forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('The reset link is invalid.', 'error')
        return redirect(url_for('password_reset.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 10 or password.lower() == password or password.upper() == password:
            flash('Password must be at least 10 characters and contain mixed case.', 'error')
            return render_template('auth/reset_password.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html')
        user.set_password(password)
        db.session.commit()
        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('password_reset.login_redirect'))
    return render_template('auth/reset_password.html')


@bp.get('/reset-login')
def login_redirect():
    from flask import redirect as flask_redirect
    return flask_redirect(url_for('auth.login'))
