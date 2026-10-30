import json
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.models import AuditLog, Job, ModerationReport, User
from app.utils.security import role_required
from app.utils.urls import is_safe_url

bp = Blueprint('moderation', __name__, url_prefix='/moderation')
REPORT_REASONS = {
    'fraud', 'impersonation', 'harassment', 'inappropriate_content', 'spam', 'other',
}


def _create_report(target_type, target_id, target_user_id=None):
    reason = request.form.get('reason', '')
    details = request.form.get('details', '').strip()
    if reason not in REPORT_REASONS or len(details) > 1000:
        flash('Choose a valid reason and keep details under 1,000 characters.', 'error')
        return False
    if target_user_id == current_user.id:
        abort(400)
    existing = ModerationReport.query.filter(
        ModerationReport.reporter_id == current_user.id,
        ModerationReport.target_type == target_type,
        ModerationReport.target_id == target_id,
        ModerationReport.status.in_(['open', 'under_review']),
    ).first()
    if existing:
        flash('You already have an open report for this item.', 'info')
        return True
    db.session.add(ModerationReport(
        reporter_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        details=details or None,
    ))
    db.session.commit()
    flash('Your report has been sent to the moderation team.', 'success')
    return True


def _report_redirect():
    referrer = request.referrer
    if referrer and is_safe_url(referrer, request.host_url):
        return redirect(referrer)
    return redirect(url_for('main.home'))


@bp.post('/users/<int:user_id>')
@login_required
@limiter.limit('5 per hour')
def report_user(user_id):
    target = db.session.get(User, user_id)
    if not target:
        abort(404)
    _create_report('user', target.id, target_user_id=target.id)
    return _report_redirect()


@bp.post('/jobs/<int:job_id>')
@login_required
@limiter.limit('5 per hour')
def report_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)
    if job.employer.user_id == current_user.id:
        abort(400)
    _create_report('job', job_id)
    return _report_redirect()


@bp.post('/reports/<int:report_id>')
@login_required
@role_required('admin')
def review_report(report_id):
    report = db.session.get(ModerationReport, report_id)
    if not report:
        abort(404)
    status = request.form.get('status')
    if status not in {'under_review', 'resolved', 'dismissed'}:
        flash('Choose a valid report status.', 'error')
        return redirect(url_for('admin.dashboard'))
    review_notes = request.form.get('review_notes', '').strip()
    if not review_notes or len(review_notes) > 2000:
        flash('Add review evidence or rationale (up to 2,000 characters) before updating the report.', 'error')
        return redirect(url_for('admin.dashboard'))
    report.status = status
    report.reviewed_by_id = current_user.id
    report.reviewed_at = datetime.utcnow()
    report.review_notes = review_notes
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='moderation_report_updated',
        entity_type=report.target_type,
        entity_id=str(report.target_id),
        metadata_json=json.dumps({
            'report_id': report.id,
            'status': status,
            'reason': report.reason,
            'review_notes': review_notes,
        }),
    ))
    db.session.commit()
    flash('Moderation report updated.', 'success')
    return redirect(url_for('admin.dashboard'))
