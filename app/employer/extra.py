from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Job, Review, Skill, TalentProfile
from app.services.matching import job_match_score
from app.utils.security import email_verified_required, role_required

bp = Blueprint('employer_extra', __name__, url_prefix='/employer')


@bp.get('/talent')
@login_required
@role_required('employer')
def talent_search():
    q = request.args.get('q', '').strip()
    city = request.args.get('city', '').strip()
    skill = request.args.get('skill', '').strip()
    query = TalentProfile.query
    if q:
        like = f'%{q}%'
        query = query.filter(TalentProfile.full_name.ilike(like) | TalentProfile.headline.ilike(like))
    if city:
        query = query.filter(TalentProfile.city.ilike(f'%{city}%'))
    talents = query.order_by(TalentProfile.trust_score.desc()).limit(80).all()
    if skill:
        talents = [t for t in talents if any(s.name.lower() == skill.lower() for s in t.skills)]
    return render_template('employer/talent_search.html', talents=talents, q=q, city=city, skill=skill, skills=Skill.query.order_by(Skill.name).all())


@bp.get('/talent/<int:profile_id>')
@login_required
@role_required('employer')
def talent_detail(profile_id):
    talent = db.session.get(TalentProfile, profile_id)
    if not talent:
        abort(404)
    return render_template('employer/talent_detail.html', talent=talent)


@bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@email_verified_required
@role_required('employer')
def edit_job(job_id):
    job = db.session.get(Job, job_id)
    if not job or job.employer_id != current_user.employer_profile.id:
        abort(404)
    if request.method == 'POST':
        job.title = request.form.get('title', '').strip()
        job.description = request.form.get('description', '').strip()
        job.category = request.form.get('category', '').strip()
        job.engagement_type = request.form.get('engagement_type', 'Apprenticeship')
        job.work_type = request.form.get('work_type', 'Hybrid')
        job.city = request.form.get('city', '').strip()
        job.remote_allowed = request.form.get('remote_allowed') == '1'
        ids = [int(v) for v in request.form.getlist('skills') if v.isdigit()]
        job.skills = Skill.query.filter(Skill.id.in_(ids)).all() if ids else []
        db.session.commit()
        flash('Opportunity updated.', 'success')
        return redirect(url_for('employer.dashboard'))
    return render_template('jobs/post.html', job=job, skills=Skill.query.order_by(Skill.category, Skill.name).all(), edit=True)
