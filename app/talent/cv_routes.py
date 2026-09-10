from pathlib import Path
from uuid import uuid4
from flask import abort, current_app, flash, redirect, send_from_directory, url_for
from flask import Blueprint, request, render_template
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import TalentProfile
from app.utils.security import role_required

bp = Blueprint('cv', __name__, url_prefix='/talent')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}


def extension_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.post('/profile/cv')
@login_required
@role_required('talent')
def upload():
    uploaded = request.files.get('cv')
    if not uploaded or not uploaded.filename:
        flash('Choose a CV file first.', 'error')
        return redirect(url_for('talent.profile'))
    if not extension_allowed(uploaded.filename):
        flash('Only PDF, DOC and DOCX files are accepted.', 'error')
        return redirect(url_for('talent.profile'))
    original = secure_filename(uploaded.filename)
    suffix = Path(original).suffix.lower()
    stored = f'{current_user.id}-{uuid4().hex}{suffix}'
    folder = Path(current_app.config['UPLOAD_FOLDER'])
    folder.mkdir(parents=True, exist_ok=True)
    uploaded.save(folder / stored)
    profile = current_user.talent_profile
    profile.cv_filename = stored
    db.session.commit()
    flash('CV uploaded securely.', 'success')
    return redirect(url_for('talent.profile'))


@bp.get('/profile/cv')
@login_required
def download_self():
    if not current_user.talent_profile or not current_user.talent_profile.cv_filename:
        abort(404)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        current_user.talent_profile.cv_filename,
        as_attachment=True,
    )


@bp.get('/talent/<int:profile_id>/cv')
@login_required
@role_required('employer', 'admin')
def download_candidate(profile_id):
    if current_user.role == 'employer' and not current_user.employer_profile.verified:
        abort(403)
    profile = db.session.get(TalentProfile, profile_id)
    if not profile or not profile.cv_filename:
        abort(404)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        profile.cv_filename,
        as_attachment=True,
    )
