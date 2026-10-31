from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def email_verified_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_email_verified:
            flash('Verify your email before using this feature.', 'error')
            return redirect(url_for('verify.notice'))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
