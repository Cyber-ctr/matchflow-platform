from datetime import date, datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Application, Apprenticeship, Review
from app.utils.security import role_required

bp = Blueprint('talent_extra', __name__)


@bp.route('/apprenticeships/<int:apprenticeship_id>', methods=['GET', 'POST'])
@login_required
@role_required('talent')
def apprenticeship(apprenticeship_id):
    item = db.session.get(Apprenticeship, apprenticeship_id)
    if not item or item.application.talent_id != current_user.talent_profile.id:
        abort(404)
    if request.method == 'POST' and request.form.get('action') == 'accept':
        if item.status == 'proposed':
            item.status = 'active'
            item.start_date = date.fromisoformat(request.form.get('start_date')) if request.form.get('start_date') else date.today()
            item.end_date = date.fromisoformat(request.form.get('end_date')) if request.form.get('end_date') else None
            db.session.commit()
            flash('Apprenticeship accepted.', 'success')
    return render_template('apprenticeships/detail.html', apprenticeship=item)


@bp.post('/apprenticeships/<int:apprenticeship_id>/review')
@login_required
@role_required('talent')
def review_apprenticeship(apprenticeship_id):
    item = db.session.get(Apprenticeship, apprenticeship_id)
    if not item or item.application.talent_id != current_user.talent_profile.id:
        abort(404)
    rating = int(request.form.get('rating', '0'))
    if rating not in range(1, 6):
        flash('Rating must be between 1 and 5.', 'error')
        return redirect(url_for('talent_extra.apprenticeship', apprenticeship_id=apprenticeship_id))
    review = Review(
        reviewer_id=current_user.id,
        reviewee_id=item.application.job.employer.user.id,
        application_id=item.application.id,
        rating=rating,
        comment=request.form.get('comment', '').strip(),
    )
    db.session.add(review)
    db.session.commit()
    flash('Thank you for your feedback.', 'success')
    return redirect(url_for('talent_extra.apprenticeship', apprenticeship_id=apprenticeship_id))
