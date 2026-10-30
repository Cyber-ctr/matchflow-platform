from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from email_validator import validate_email, EmailNotValidError

from app.extensions import db, limiter
from app.models import EmployerProfile, TalentProfile, User
from app.utils.urls import is_safe_url

bp = Blueprint('auth', __name__, url_prefix='/auth')


def safe_role(value):
    return value if value in {'talent', 'employer'} else 'talent'


@bp.get('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('auth/login.html')


@bp.post('/login')
@limiter.limit('10 per minute')
def login_post():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not user.check_password(password) or not user.is_active:
        flash('Invalid email or password.', 'error')
        return render_template('auth/login.html'), 401
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    login_user(user, remember=request.form.get('remember') == '1')
    from flask import session
    session.permanent = True
    next_url = request.args.get('next')
    if not is_safe_url(next_url, request.host_url):
        next_url = url_for('dashboard')
    return redirect(next_url)


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per hour', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'GET':
        return render_template('auth/register.html')
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    role = safe_role(request.form.get('role'))
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        flash(str(exc), 'error')
        return render_template('auth/register.html'), 400
    if len(password) < 10 or password.lower() == password or password.upper() == password:
        flash('Password must be at least 10 characters and contain mixed case.', 'error')
        return render_template('auth/register.html'), 400
    if password != confirm:
        flash('Passwords do not match.', 'error')
        return render_template('auth/register.html'), 400
    if db.session.execute(select(User).where(User.email == email)).scalar_one_or_none():
        flash('An account with that email already exists.', 'error')
        return render_template('auth/register.html'), 409

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    if role == 'talent':
        name = request.form.get('full_name', '').strip()
        if not name:
            flash('Please provide your full name.', 'error')
            db.session.rollback()
            return render_template('auth/register.html'), 400
        db.session.add(TalentProfile(user_id=user.id, full_name=name, headline='Junior professional'))
    else:
        business = request.form.get('business_name', '').strip()
        if not business:
            flash('Please provide your business name.', 'error')
            db.session.rollback()
            return render_template('auth/register.html'), 400
        db.session.add(EmployerProfile(user_id=user.id, business_name=business))
    db.session.commit()
    from app.auth.verify_routes import build_token
    from app.services.email import send_email
    from flask import current_app
    verify_url = url_for('verify.verify', token=build_token(user.email), _external=True)
    if send_email(user.email, 'Verify your MatchFlow email', f'Verify your MatchFlow account within 24 hours:\n\n{verify_url}'):
        current_app.logger.info('Verification email sent')
    else:
        if current_app.config.get('TESTING') or current_app.debug:
            current_app.logger.info('SMTP is not configured; verification email was not sent')
        else:
            current_app.logger.warning('Verification email could not be delivered')
    login_user(user)
    flash('Welcome to MatchFlow. Complete your profile to start matching.', 'success')
    return redirect(url_for('dashboard'))


@bp.post('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))


@bp.post('/account/delete')
@login_required
def delete_account():
    import uuid
    if not current_user.check_password(request.form.get('password', '')):
        flash('Password confirmation failed. Your account was not deactivated.', 'error')
        return redirect(url_for('dashboard'))
    user = current_user
    # Anonymise rather than hard-delete so marketplace/audit relationships remain intact.
    user.email = f'deleted-{uuid.uuid4().hex[:16]}@invalid.matchflow'
    user.is_active = False
    user.is_email_verified = False
    user.password_hash = uuid.uuid4().hex
    if user.talent_profile:
        profile = user.talent_profile
        profile.full_name = 'Deleted MatchFlow User'
        profile.phone = None
        profile.city = None
        profile.bio = None
        profile.portfolio_url = None
        profile.github_url = None
        profile.linkedin_url = None
        profile.cv_filename = None
        profile.verification_status = 'unverified'
    if user.employer_profile:
        profile = user.employer_profile
        profile.business_name = 'Deleted MatchFlow Business'
        profile.phone = None
        profile.city = None
        profile.description = None
        profile.website = None
        profile.registration_number = None
        profile.verified = False
    db.session.commit()
    logout_user()
    flash('Your MatchFlow account has been deactivated and personal profile data anonymised.', 'success')
    return redirect(url_for('main.home'))
