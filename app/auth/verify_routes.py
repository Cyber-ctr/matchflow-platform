from flask import Blueprint, flash, redirect, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db
from app.models import User

bp = Blueprint('verify', __name__, url_prefix='/auth')


def serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='matchflow-email-verify')


def build_token(email):
    return serializer().dumps(email)


@bp.get('/verify/<token>')
def verify(token):
    try:
        email = serializer().loads(token, max_age=86400)
    except (BadSignature, SignatureExpired):
        flash('That email verification link is invalid or expired.', 'error')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('auth.login'))
    user.is_email_verified = True
    db.session.commit()
    flash('Email verified. Your MatchFlow account is now verified.', 'success')
    return redirect(url_for('dashboard'))
