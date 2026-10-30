import json

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AuditLog, EmployerProfile, Job, ModerationReport, TalentProfile, User
from app.utils.security import role_required

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
@role_required('admin')
def verify_talent(profile_id):
    profile = db.session.get(TalentProfile, profile_id)
    if not profile:
        abort(404)
    profile.verification_status = 'verified'
    profile.trust_score = max(80, profile.trust_score)
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='talent_verified',
        entity_type='talent_profile',
        entity_id=str(profile.id),
    ))
    db.session.commit()
    flash('Talent verified.', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.post('/employers/<int:profile_id>/verify')
@login_required
@role_required('admin')
def verify_employer(profile_id):
    profile = db.session.get(EmployerProfile, profile_id)
    if not profile:
        abort(404)
    profile.verified = True
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='employer_verified',
        entity_type='employer_profile',
        entity_id=str(profile.id),
    ))
    db.session.commit()
    flash('Employer verified.', 'success')
    return redirect(url_for('admin.dashboard'))
