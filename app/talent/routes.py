from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.extensions import db, limiter
from app.models import Application, AuditLog, Job, Notification, SavedJob, Skill
from app.services.matching import recommended_jobs
from app.services.notifications import notify
from app.utils.security import email_verified_required, role_required
from app.utils.time import utcnow_naive

bp = Blueprint('talent', __name__, url_prefix='/talent')


@bp.get('/dashboard')
@login_required
@role_required('talent')
def dashboard():
    talent = current_user.talent_profile
    jobs = Job.query.filter_by(status='published').order_by(Job.created_at.desc()).limit(50).all()
    recs = recommended_jobs(talent, jobs, limit=5)
    apps = Application.query.filter_by(talent_id=talent.id).order_by(Application.created_at.desc()).limit(8).all()
    return render_template('talent/dashboard.html', talent=talent, recommendations=recs, applications=apps)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('talent')
def profile():
    talent = current_user.talent_profile
    if request.method == 'POST':
        talent.full_name = request.form.get('full_name', '').strip()
        talent.headline = request.form.get('headline', '').strip()
        talent.phone = request.form.get('phone', '').strip()
        talent.city = request.form.get('city', '').strip()
        talent.bio = request.form.get('bio', '').strip()
        talent.education = request.form.get('education', '').strip()
        talent.experience_level = request.form.get('experience_level', 'Junior')
        talent.availability = request.form.get('availability', 'Available')
        try:
            talent.expected_rate = float(request.form['expected_rate']) if request.form.get('expected_rate') else None
        except ValueError:
            talent.expected_rate = None
        talent.portfolio_url = request.form.get('portfolio_url', '').strip()
        talent.github_url = request.form.get('github_url', '').strip()
        talent.linkedin_url = request.form.get('linkedin_url', '').strip()
        skill_ids = [int(value) for value in request.form.getlist('skills') if value.isdigit()]
        talent.skills = Skill.query.filter(Skill.id.in_(skill_ids)).all() if skill_ids else []
        talent.trust_score = min(100, 20 + len(talent.skills) * 10 + (15 if talent.portfolio_url else 0))
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('talent.profile'))
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    return render_template('talent/profile.html', talent=talent, skills=skills)


@bp.post('/jobs/<int:job_id>/apply')
@login_required
@email_verified_required
@limiter.limit('20 per hour')
@role_required('talent')
def apply(job_id):
    job = db.session.get(Job, job_id)
    if not job or job.status != 'published':
        flash('That opportunity is no longer available.', 'error')
        return redirect(url_for('main.jobs'))
    talent = current_user.talent_profile
    existing = Application.query.filter_by(job_id=job.id, talent_id=talent.id).first()
    if existing:
        flash('You have already applied to this opportunity.', 'info')
        return redirect(url_for('main.job_detail', job_id=job.id))
    cover_letter = request.form.get('cover_letter', '').strip()
    if len(cover_letter) > 5000:
        flash('Cover letter is too long.', 'error')
        return redirect(url_for('main.job_detail', job_id=job.id))
    application = Application(
        job_id=job.id,
        talent_id=talent.id,
        cover_letter=cover_letter,
    )
    db.session.add(application)
    db.session.flush()
    notify(job.employer.user, 'New application', f'{talent.full_name} applied for {job.title}.', url_for('employer.applicants', job_id=job.id))
    db.session.commit()
    flash('Application submitted successfully.', 'success')
    return redirect(url_for('talent.applications'))


@bp.post('/verification/request')
@login_required
@email_verified_required
@limiter.limit('3 per hour')
@role_required('talent')
def request_verification():
    talent = current_user.talent_profile
    if talent.verification_status == 'pending':
        flash('Your verification request is already being reviewed.', 'info')
        return redirect(url_for('talent.profile'))
    talent.verification_status = 'pending'
    talent.verification_request_note = request.form.get(
        'verification_note', '',
    ).strip()[:1000] or None
    talent.verification_review_notes = None
    talent.verification_requested_at = utcnow_naive()
    db.session.add(AuditLog(
        actor_id=current_user.id,
        action='talent_verification_requested',
        entity_type='talent_profile',
        entity_id=str(talent.id),
    ))
    db.session.commit()
    flash('Your verification request has been submitted for review.', 'success')
    return redirect(url_for('talent.profile'))


@bp.post('/jobs/<int:job_id>/save')
@login_required
@role_required('talent')
def save_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        flash('Opportunity not found.', 'error')
        return redirect(url_for('main.jobs'))
    saved = SavedJob.query.filter_by(talent_id=current_user.talent_profile.id, job_id=job.id).first()
    if saved:
        db.session.delete(saved)
        flash('Opportunity removed from your saved list.', 'success')
    else:
        db.session.add(SavedJob(talent_id=current_user.talent_profile.id, job_id=job.id))
        flash('Opportunity saved.', 'success')
    db.session.commit()
    return redirect(url_for('main.job_detail', job_id=job.id))


@bp.get('/applications')
@login_required
@role_required('talent')
def applications():
    applications = Application.query.filter_by(talent_id=current_user.talent_profile.id).order_by(Application.created_at.desc()).all()
    return render_template('talent/applications.html', applications=applications)


@bp.get('/saved')
@login_required
@role_required('talent')
def saved():
    items = SavedJob.query.filter_by(talent_id=current_user.talent_profile.id).order_by(SavedJob.created_at.desc()).all()
    return render_template('talent/saved.html', saved=items)


@bp.get('/notifications')
@login_required
def notifications():
    items = current_user.notifications.order_by(Notification.created_at.desc()).all()
    for item in items:
        if not item.read_at:
            item.read_at = utcnow_naive()
    db.session.commit()
    return render_template('main/notifications.html', notifications=items)
