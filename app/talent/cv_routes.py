from pathlib import Path
from flask import abort, flash, redirect, send_file, url_for
from flask import Blueprint, request, render_template
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import TalentProfile, User
from app.services.storage import get_storage
from app.utils.security import role_required

bp = Blueprint('cv', __name__, url_prefix='/talent')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
AVATAR_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}


def extension_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.post('/profile/cv')
@login_required
@role_required('talent')
def upload():
    if not current_user.talent_profile:
        abort(404)
    uploaded = request.files.get('cv')
    if not uploaded or not uploaded.filename:
        flash('Choose a CV file first.', 'error')
        return redirect(url_for('talent.profile'))
    if not extension_allowed(uploaded.filename):
        flash('Only PDF, DOC and DOCX files are accepted.', 'error')
        return redirect(url_for('talent.profile'))
    original = secure_filename(uploaded.filename)
    suffix = Path(original).suffix.lower()
    stored = get_storage().save(
        uploaded.stream, 'cvs', current_user.id, suffix, uploaded.mimetype,
    )
    profile = current_user.talent_profile
    profile.cv_filename = stored
    db.session.commit()
    flash('CV uploaded securely.', 'success')
    return redirect(url_for('talent.profile'))


@bp.post('/profile/avatar')
@login_required
@role_required('talent')
def upload_avatar():
    if not current_user.talent_profile:
        abort(404)
    uploaded = request.files.get('avatar')
    if not uploaded or not uploaded.filename:
        flash('Choose an avatar image first.', 'error')
        return redirect(url_for('talent.profile'))
    if not extension_allowed_for(uploaded.filename, AVATAR_EXTENSIONS):
        flash('Only JPG, PNG and WEBP images are accepted.', 'error')
        return redirect(url_for('talent.profile'))
    suffix = Path(secure_filename(uploaded.filename)).suffix.lower()
    key = get_storage().save(
        uploaded.stream, 'avatars', current_user.id, suffix, uploaded.mimetype,
    )
    current_user.talent_profile.avatar_filename = key
    db.session.commit()
    flash('Profile photo uploaded.', 'success')
    return redirect(url_for('talent.profile'))


@bp.get('/profile/cv')
@login_required
def download_self():
    if not current_user.talent_profile or not current_user.talent_profile.cv_filename:
        abort(404)
    try:
        content = get_storage().open(current_user.talent_profile.cv_filename)
    except FileNotFoundError:
        abort(404)
    response = send_file(
        content, as_attachment=True,
        download_name=Path(current_user.talent_profile.cv_filename).name,
        mimetype='application/octet-stream',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@bp.get('/talent/<int:profile_id>/cv')
@login_required
@role_required('employer', 'admin')
def download_candidate(profile_id):
    if current_user.role == 'employer' and (
        not current_user.employer_profile
        or not current_user.employer_profile.verified
    ):
        abort(403)
    profile = db.session.get(TalentProfile, profile_id)
    if not profile or not profile.cv_filename:
        abort(404)
    try:
        content = get_storage().open(profile.cv_filename)
    except FileNotFoundError:
        abort(404)
    response = send_file(
        content, as_attachment=True,
        download_name=Path(profile.cv_filename).name,
        mimetype='application/octet-stream',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@bp.get('/<int:user_id>/avatar')
@login_required
def download_avatar(user_id):
    user = db.session.get(User, user_id)
    if not user or not user.talent_profile or not user.talent_profile.avatar_filename:
        abort(404)
    if current_user.id != user.id and current_user.role != 'admin':
        if (
            current_user.role != 'employer'
            or not current_user.employer_profile
            or not current_user.employer_profile.verified
        ):
            abort(403)
    try:
        content = get_storage().open(user.talent_profile.avatar_filename)
    except FileNotFoundError:
        abort(404)
    response = send_file(
        content, as_attachment=False,
        download_name=Path(user.talent_profile.avatar_filename).name,
        mimetype={
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }.get(Path(user.talent_profile.avatar_filename).suffix.lower(), 'application/octet-stream'),
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response


def extension_allowed_for(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions
