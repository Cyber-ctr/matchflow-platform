from flask import Blueprint, abort, render_template, request
from flask_login import current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Job
from app.services.matching import job_match_score

bp = Blueprint('main', __name__)


@bp.get('/')
def home():
    featured = Job.query.filter_by(status='published').order_by(Job.created_at.desc()).limit(6).all()
    return render_template('main/home.html', featured=featured)


@bp.get('/jobs')
def jobs():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    city = request.args.get('city', '').strip()
    engagement = request.args.get('engagement', '').strip()

    query = Job.query.filter_by(status='published')
    if q:
        term = f'%{q}%'
        query = query.filter(or_(Job.title.ilike(term), Job.description.ilike(term)))
    if category:
        query = query.filter(Job.category == category)
    if city:
        query = query.filter(Job.city.ilike(f'%{city}%'))
    if engagement:
        query = query.filter(Job.engagement_type == engagement)
    listings = query.order_by(Job.created_at.desc()).all()
    return render_template('jobs/list.html', jobs=listings, q=q, category=category, city=city, engagement=engagement)


@bp.get('/jobs/<int:job_id>')
def job_detail(job_id):
    job = db.session.get(Job, job_id)
    if not job or job.status != 'published':
        abort(404)
    job.views += 1
    db.session.commit()
    score = None
    applied = False
    saved = False
    if current_user.is_authenticated and current_user.talent_profile:
        score = job_match_score(current_user.talent_profile, job)
        applied = any(app.job_id == job.id for app in current_user.talent_profile.applications)
        saved = any(item.job_id == job.id for item in current_user.talent_profile.saved_jobs)
    return render_template('jobs/detail.html', job=job, match_score=score, applied=applied, saved=saved)


@bp.get('/about')
def about():
    return render_template('main/about.html')


@bp.get('/privacy')
def privacy():
    return render_template('main/privacy.html')


@bp.get('/terms')
def terms():
    return render_template('main/terms.html')
