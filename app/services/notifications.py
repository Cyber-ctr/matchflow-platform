from app.extensions import db
from app.models import Notification


def notify(user, title, body, link=None):
    notice = Notification(user_id=user.id, title=title, body=body, link=link)
    db.session.add(notice)
    return notice
