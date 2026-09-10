from flask import Blueprint, jsonify, request
from sqlalchemy import text
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Job
from app.services.matching import job_match_score

bp = Blueprint('api', __name__, url_prefix='/api/v1')


@bp.get('/health')
def health():
    try:
        db.session.execute(text('SELECT 1'))
    except Exception:
        db.session.rollback()
        return jsonify({'status': 'degraded', 'service': 'matchflow'}), 503
    return jsonify({'status': 'ok', 'service': 'matchflow', 'database': 'ok'})


@bp.get('/jobs')
def public_jobs():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    query = Job.query.filter_by(status='published')
    if q:
        like = f'%{q}%'
        query = query.filter(Job.title.ilike(like))
    if category:
        query = query.filter_by(category=category)
    jobs = query.order_by(Job.created_at.desc()).limit(50).all()
    return jsonify({
        'items': [
            {
                'id': job.id,
                'title': job.title,
                'category': job.category,
                'city': job.city,
                'engagement_type': job.engagement_type,
                'work_type': job.work_type,
                'salary_min': float(job.salary_min) if job.salary_min else None,
                'salary_max': float(job.salary_max) if job.salary_max else None,
            }
            for job in jobs
        ],
    })


@bp.get('/me')
@login_required
def me():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'display_name': current_user.display_name,
    })
