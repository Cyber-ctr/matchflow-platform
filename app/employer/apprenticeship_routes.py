from flask import abort, flash, redirect, render_template, request, url_for
from flask import Blueprint
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Apprenticeship, Review
from app.utils.security import role_required

bp = Blueprint('employer_apprenticeships', __name__, url_prefix='/employer')


@bp.route('/apprenticeships/<int:apprenticeship_id>', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def detail(apprenticeship_id):
    item = db.session.get(Apprenticeship, apprenticeship_id)
    if not item or item.application.job.employer_id != current_user.employer_profile.id:
        abort(404)
    if request.method == 'POST':
        status = request.form.get('status')
        if status in {'active', 'paused', 'completed', 'cancelled'}:
            item.status = status
        item.supervisor_name = request.form.get('supervisor_name', '').strip()
        item.supervisor_phone = request.form.get('supervisor_phone', '').strip()
        item.objectives = request.form.get('objectives', '').strip()
        item.terms = request.form.get('terms', '').strip()
        item.allowance = float(request.form['allowance']) if request.form.get('allowance') else None
        db.session.commit()
        flash('Apprenticeship record updated.', 'success')
    return render_template('apprenticeships/employer_detail.html', apprenticeship=item)


@bp.post('/apprenticeships/<int:apprenticeship_id>/review')
@login_required
@role_required('employer')
def review(apprenticeship_id):
    item = db.session.get(Apprenticeship, apprenticeship_id)
    if not item or item.application.job.employer_id != current_user.employer_profile.id:
        abort(404)
    rating = int(request.form.get('rating', '0'))
    if rating not in range(1, 6):
        flash('Rating must be between 1 and 5.', 'error')
        return redirect(url_for('employer_apprenticeships.detail', apprenticeship_id=apprenticeship_id))
    db.session.add(Review(
        reviewer_id=current_user.id,
        reviewee_id=item.application.talent.user.id,
        application_id=item.application.id,
        rating=rating,
        comment=request.form.get('comment', '').strip(),
    ))
    db.session.commit()
    flash('Talent feedback submitted.', 'success')
    return redirect(url_for('employer_apprenticeships.detail', apprenticeship_id=apprenticeship_id))
