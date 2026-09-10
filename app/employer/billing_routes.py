from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Payment
from app.services.payments import PaymentService
from app.utils.security import role_required

bp = Blueprint('billing', __name__, url_prefix='/employer')

PLANS = {
    'starter': {'name': 'Starter', 'price': 15000, 'description': '1 active opportunity, basic candidate search.'},
    'growth': {'name': 'Growth', 'price': 35000, 'description': '5 active opportunities, advanced candidate search and priority support.'},
    'scale': {'name': 'Scale', 'price': 75000, 'description': 'Unlimited opportunities, priority matching and employer analytics.'},
}


@bp.get('/billing')
@login_required
@role_required('employer')
def billing():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(20).all()
    return render_template('employer/billing.html', plans=PLANS, payments=payments)


@bp.post('/billing/checkout')
@login_required
@role_required('employer')
def checkout():
    plan_key = request.form.get('plan')
    provider = request.form.get('provider', 'manual')
    plan = PLANS.get(plan_key)
    if not plan or provider not in {'manual', 'mtn_momo', 'orange_money'}:
        flash('Invalid plan or payment provider.', 'error')
        return redirect(url_for('billing.billing'))
    payment = PaymentService().create_pending(
        current_user,
        plan['price'],
        f"employer_subscription:{plan_key}",
        provider=provider,
    )
    db.session.commit()
    flash(
        f"Checkout reference {payment.reference} created. Connect the provider gateway to complete payment.",
        'info',
    )
    return redirect(url_for('billing.billing'))
