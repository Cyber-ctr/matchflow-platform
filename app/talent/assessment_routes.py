import json
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Assessment, AssessmentAttempt
from app.utils.security import role_required
from app.utils.time import utcnow_naive

bp = Blueprint('assessment', __name__, url_prefix='/assessments')


@bp.get('/')
@login_required
@role_required('talent')
def index():
    assessments = Assessment.query.filter_by(is_active=True).order_by(Assessment.category, Assessment.name).all()
    attempts = AssessmentAttempt.query.filter_by(user_id=current_user.id).order_by(AssessmentAttempt.created_at.desc()).all()
    latest = {a.assessment_id: a for a in attempts}
    return render_template('talent/assessments.html', assessments=assessments, latest=latest)


@bp.route('/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
@role_required('talent')
def take(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment or not assessment.is_active:
        abort(404)
    if request.method == 'POST':
        total = sum(question.points for question in assessment.questions) or 1
        earned = 0
        for question in assessment.questions:
            try:
                answer = int(request.form.get(f'q_{question.id}', '-1'))
            except ValueError:
                answer = -1
            if answer == question.correct_index:
                earned += question.points
        score = round(earned * 100 / total)
        attempt = AssessmentAttempt(
            user_id=current_user.id,
            assessment_id=assessment.id,
            score=score,
            passed=score >= assessment.pass_score,
            completed_at=utcnow_naive(),
        )
        db.session.add(attempt)
        if current_user.talent_profile:
            current_user.talent_profile.trust_score = min(
                100, current_user.talent_profile.trust_score + (10 if attempt.passed else 2)
            )
        db.session.commit()
        flash(f'Assessment completed. Your score: {score}%.', 'success' if attempt.passed else 'info')
        return redirect(url_for('assessment.index'))
    for q in assessment.questions:
        json.loads(q.choices)
    return render_template('talent/assessment_take.html', assessment=assessment)
