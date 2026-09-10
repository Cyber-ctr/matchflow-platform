import uuid
from app.extensions import db
from app.models import Payment


class PaymentService:
    """Provider-neutral payment layer.

    Configure a real Mobile Money gateway behind this interface in production.
    The MVP deliberately stores a pending transaction rather than pretending to
    complete a live MTN/Orange transaction without merchant credentials.
    """

    def create_pending(self, user, amount, purpose, provider='manual'):
        payment = Payment(
            user_id=user.id,
            reference=f'MF-{uuid.uuid4().hex[:12].upper()}',
            provider=provider,
            amount=amount,
            purpose=purpose,
            status='pending',
        )
        db.session.add(payment)
        db.session.flush()
        return payment
