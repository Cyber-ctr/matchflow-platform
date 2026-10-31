from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.extensions import db, limiter
from app.models import Application, Apprenticeship, AuditLog, Job, Notification, Skill
from app.services.notifications import notify
from app.utils.security import email_verified_required, role_required
from app.utils.time import utcnow_naive

bp = Blueprint('employer', __name__, url_prefix='/employer')


@bp.get('/dashboard')
@login_required
@role_required('employer')
def dashboard():
    employer = current_user.employer_profile
    jobs = Job.query.filter_by(employer_id=employer.id).order_by(Job.created_at.desc()).all()
    active_jobs = sum(1 for job in jobs if job.status == 'published')
    app_count = sum(len(job.applications) for job in jobs)
    return render_template('employer/dashboard.html', employer=employer, jobs=jobs, active_jobs=active_jobs, app_count=app_count)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def profile():
    profile = current_user.employer_profile
    if request.method == 'POST':
        profile.business_name = request.form.get('business_name', '').strip()
        profile.industry = request.form.get('industry', '').strip()
        profile.description = request.form.get('description', '').strip()
        profile.city = request.form.get('city', '').strip()
        profile.phone = request.form.get('phone', '').strip()
        profile.website = request.form.get('website', '').strip()
        profile.registration_number = request.form.get('registration_number', '').strip()
        db.session.commit()
        flash('Business profile updated.', 'success')
        return redirect(url_for('employer.profile'))
    return render_template('employer/profile.html', employer=profile)


@bp.route('/jobs/new', methods=['GET', 'POST'])
@login_required
@email_verified_required
@limiter.limit('20 per hour', methods=['POST'])
@role_required('employer')
def new_job():
    if request.method == 'GET':
        return render_template('jobs/post.html', skills=Skill.query.order_by(Skill.category, Skill.name).all(), job=None)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    allowed_categories = {'Frontend Development', 'Graphic Design', 'Bookkeeping'}
    allowed_engagement = {'Apprenticeship', 'Freelance', 'Part-time', 'Full-time'}
    allowed_work = {'Hybrid', 'Remote', 'On-site'}
    if not title or not description or category not in allowed_categories:
        flash('Title, description and a valid category are required.', 'error')
        return render_template('jobs/post.html', skills=Skill.query.order_by(Skill.category, Skill.name).all(), job=None), 400
    engagement = request.form.get('engagement_type', 'Apprenticeship')
    work_type = request.form.get('work_type', 'Hybrid')
    if engagement not in allowed_engagement or work_type not in allowed_work:
        flash('Invalid engagement or work type.', 'error')
        return render_template('jobs/post.html', skills=Skill.query.order_by(Skill.category, Skill.name).all(), job=None), 400
    job = Job(
        employer_id=current_user.employer_profile.id,
        title=title,
        description=description,
        category=category,
        engagement_type=engagement,
        work_type=work_type,
        city=request.form.get('city', '').strip(),
        remote_allowed=request.form.get('remote_allowed') == '1',
        duration_weeks=int(request.form['duration_weeks']) if request.form.get('duration_weeks', '').isdigit() else None,
        salary_min=float(request.form['salary_min']) if request.form.get('salary_min') else None,
        salary_max=float(request.form['salary_max']) if request.form.get('salary_max') else None,
        status='published',
    )
    ids = [int(v) for v in request.form.getlist('skills') if v.isdigit()]
    job.skills = Skill.query.filter(Skill.id.in_(ids)).all() if ids else []
    db.session.add(job)
    db.session.commit()
    flash('Opportunity published.', 'success')
    return redirect(url_for('employer.dashboard'))


@bp.post('/verification/request')
@login_required
@email_verified_required
@limiter.limit('3 per hour')
@role_required('employer')
def request_verification():
    employer = current_user.employer_profile
    if employer.verification_status == 'pending':
        flash('Your business verification request is already being reviewed.', 'info')
        return redirect(url_for('employer.profile'))
    employer.verification_status = 'pending'
    employer.verified = False
    employer.verification_request_note = request.form.get(
        'verification_note', '',
    ).strip()[:1000] or None
    employer.verification_review_notes = None
    employer.verification_requested_at = utcnow_naive()
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='employer_verification_requested',
        entity_type='employer_profile',
        entity_id=str(employer.id),
    ))
    db.session.commit()
    flash('Your business verification request has been submitted for review.', 'success')
    return redirect(url_for('employer.profile'))


@bp.post('/jobs/<int:job_id>/close')
@login_required
@role_required('employer')
def close_job(job_id):
    job = db.session.get(Job, job_id)
    if not job or job.employer_id != current_user.employer_profile.id:
        return 'Not found', 404
    job.status = 'closed'
    db.session.commit()
    flash('Opportunity closed.', 'success')
    return redirect(url_for('employer.dashboard'))


@bp.get('/jobs/<int:job_id>/applicants')
@login_required
@role_required('employer')
def applicants(job_id):
    job = db.session.get(Job, job_id)
    if not job or job.employer_id != current_user.employer_profile.id:
        return 'Not found', 404
    return render_template('employer/applicants.html', job=job, applications=job.applications)


@bp.post('/applications/<int:application_id>/status')
@login_required
@role_required('employer')
def application_status(application_id):
    app = db.session.get(Application, application_id)
    if not app or app.job.employer_id != current_user.employer_profile.id:
        return 'Not found', 404
    status = request.form.get('status', 'submitted')
    allowed = {'submitted', 'shortlisted', 'interview', 'accepted', 'rejected'}
    if status not in allowed:
        flash('Invalid application status.', 'error')
        return redirect(url_for('employer.applicants', job_id=app.job_id))
    app.status = status
    note = request.form.get('employer_note', '').strip()
    if note:
        app.employer_note = note
    if status == 'accepted' and not app.apprenticeship and app.job.engagement_type == 'Apprenticeship':
        apprenticeship = Apprenticeship(application_id=app.id, status='proposed')
        db.session.add(apprenticeship)
    notify(app.talent.user, 'Application update', f'Your application for {app.job.title} is now {status}.', url_for('talent.applications'))
    db.session.commit()
    flash('Application updated.', 'success')
    return redirect(url_for('employer.applicants', job_id=app.job_id))
