from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db, limiter
from app.models import Message, Notification, User
from app.services.notifications import notify

bp = Blueprint('messaging', __name__, url_prefix='/messages')


@bp.get('/')
@login_required
def index():
    sent_ids = {m.receiver_id for m in Message.query.filter_by(sender_id=current_user.id).all()}
    received_ids = {m.sender_id for m in Message.query.filter_by(receiver_id=current_user.id).all()}
    ids = (sent_ids | received_ids) - {current_user.id}
    contacts = User.query.filter(User.id.in_(ids)).order_by(User.created_at.desc()).all() if ids else []
    return render_template('messaging/index.html', contacts=contacts)


@bp.route('/<int:user_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit('60 per hour', methods=['POST'])
def thread(user_id):
    other = db.session.get(User, user_id)
    if not other or other.id == current_user.id:
        return redirect(url_for('messaging.index'))
    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if not body or len(body) > 4000:
            flash('Message must be between 1 and 4000 characters.', 'error')
            return redirect(url_for('messaging.thread', user_id=user_id))
        message = Message(sender_id=current_user.id, receiver_id=user_id, body=body)
        db.session.add(message)
        notify(other, 'New MatchFlow message', f'{current_user.display_name} sent you a message.', url_for('messaging.thread', user_id=current_user.id))
        db.session.commit()
        return redirect(url_for('messaging.thread', user_id=user_id))
    messages = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.receiver_id == user_id),
            (Message.sender_id == user_id) & (Message.receiver_id == current_user.id),
        )
    ).order_by(Message.created_at.asc()).all()
    for item in messages:
        if item.receiver_id == current_user.id and not item.read_at:
            item.read_at = datetime.utcnow()
    db.session.commit()
    return render_template('messaging/thread.html', other=other, messages=messages)
