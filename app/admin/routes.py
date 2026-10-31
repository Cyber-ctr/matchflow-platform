import json

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AuditLog, EmployerProfile, Job, ModerationReport, TalentProfile, User
from app.utils.security import email_verified_required, role_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.get('/')
@login_required
@role_required('admin')
def dashboard():
    return render_template(
        'admin/dashboard.html',
        users=User.query.order_by(User.created_at.desc()).limit(20).all(),
        jobs=Job.query.order_by(Job.created_at.desc()).limit(20).all(),
        talent_count=TalentProfile.query.count(),
        employer_count=EmployerProfile.query.count(),
        job_count=Job.query.count(),
        reports=ModerationReport.query.filter(
            ModerationReport.status.in_(['open', 'under_review']),
        ).order_by(ModerationReport.created_at.asc()).limit(50).all(),
        pending_talents=TalentProfile.query.filter_by(
            verification_status='pending',
        ).order_by(TalentProfile.verification_requested_at.asc()).limit(50).all(),
        pending_employers=EmployerProfile.query.filter_by(
            verification_status='pending',
        ).order_by(EmployerProfile.verification_requested_at.asc()).limit(50).all(),
    )


@bp.post('/users/<int:user_id>/toggle')
@login_required
@role_required('admin')
def toggle_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.id == current_user.id:
        abort(404)
    user.is_active = not user.is_active
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='user_status_toggled',
        entity_type='user',
        entity_id=str(user.id),
        metadata_json=json.dumps({'is_active': user.is_active}),
    ))
    db.session.commit()
    flash('User status updated.', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.post('/talent/<int:profile_id>/verify')
@login_required
@email_verified_required
@role_required('admin')
def verify_talent(profile_id):
    profile = db.session.get(TalentProfile, profile_id)
    if not profile:
        abort(404)
    return review_verification(profile, 'talent_profile')


@bp.post('/employers/<int:profile_id>/verify')
@login_required
@email_verified_required
@role_required('admin')
def verify_employer(profile_id):
    profile = db.session.get(EmployerProfile, profile_id)
    if not profile:
        abort(404)
    return review_verification(profile, 'employer_profile')


def review_verification(profile, entity_type):
    status = request.form.get('status', '')
    notes = request.form.get('review_notes', '').strip()
    if status not in {'verified', 'rejected'}:
        flash('Choose whether to approve or reject this request.', 'error')
        return redirect(url_for('admin.dashboard'))
    if not notes or len(notes) > 2000:
        flash('Add a review rationale of no more than 2000 characters.', 'error')
        return redirect(url_for('admin.dashboard'))
    if profile.verification_status != 'pending':
        flash('Only pending verification requests can be reviewed.', 'error')
        return redirect(url_for('admin.dashboard'))

    profile.verification_status = status
    profile.verification_review_notes = notes
    if entity_type == 'talent_profile' and status == 'verified':
        profile.trust_score = max(80, profile.trust_score)
    if entity_type == 'employer_profile':
        profile.verified = status == 'verified'
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action=f'{entity_type}_verification_{status}',
        entity_type=entity_type,
        entity_id=str(profile.id),
        metadata_json=json.dumps({'review_notes': notes}),
    ))
    db.session.commit()
    flash(
        f'Verification request {"approved" if status == "verified" else "rejected"}.',
        'success',
    )
    return redirect(url_for('admin.dashboard'))
