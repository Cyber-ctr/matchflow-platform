from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db, limiter
from app.models import User
from app.services.email import send_email

bp = Blueprint('verify', __name__, url_prefix='/auth')


def serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='matchflow-email-verify')


def build_token(email):
    return serializer().dumps(email)


def send_verification_email(user):
    verify_url = url_for(
        'verify.verify', token=build_token(user.email), _external=True,
    )
    return send_email(
        user.email,
        'Verify your MatchFlow email',
        f'Verify your MatchFlow account within 24 hours:\n\n{verify_url}',
    )


@bp.get('/verify')
@login_required
def notice():
    return render_template('auth/verify_notice.html')


@bp.post('/verify/resend')
@login_required
@limiter.limit('3 per hour')
def resend():
    if current_user.is_email_verified:
        flash('Your email is already verified.', 'info')
    elif send_verification_email(current_user):
        flash('A new verification link has been sent to your email.', 'success')
    else:
        current_app.logger.warning(
            'Verification email could not be delivered for user_id=%s',
            current_user.id,
        )
        flash('We could not send the verification email. Please try again later.', 'error')
    return redirect(url_for('verify.notice'))


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
    if not user.is_active:
        flash('This account is no longer active.', 'error')
        return redirect(url_for('auth.login'))
    user.is_email_verified = True
    db.session.commit()
    flash('Your email address is verified.', 'success')
    return redirect(url_for('dashboard'))
