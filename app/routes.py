from flask import redirect, url_for
from flask_login import login_required, current_user


def dashboard():
    if current_user.role == 'talent':
        return redirect(url_for('talent.dashboard'))
    if current_user.role == 'employer':
        return redirect(url_for('employer.dashboard'))
    return redirect(url_for('admin.dashboard'))
