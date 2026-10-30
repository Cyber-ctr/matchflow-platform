import json

from flask import Blueprint, abort, flash, redirect, request, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.models import AuditLog, Job
from app.utils.security import role_required

bp = Blueprint('admin_jobs', __name__, url_prefix='/admin')


@bp.post('/jobs/<int:job_id>/status')
@login_required
@role_required('admin')
def status(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)
    new_status = request.form.get('status')
    if new_status not in {'published', 'closed', 'suspended'}:
        flash('Invalid job status.', 'error')
        return redirect(url_for('admin.dashboard'))
    job.status = new_status
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='job_status_updated',
        entity_type='job',
        entity_id=str(job.id),
        metadata_json=json.dumps({'status': new_status}),
    ))
    db.session.commit()
    flash('Job status updated.', 'success')
    return redirect(url_for('admin.dashboard'))
