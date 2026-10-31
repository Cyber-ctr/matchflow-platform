from app.extensions import db
from app.models import (
    Application, AuditLog, EmployerProfile, Job, Payment, TalentProfile, User,
)


def create_user(role, email, verified=False):
    user = User(email=email, role=role, is_email_verified=verified)
    user.set_password('StrongPass123')
    db.session.add(user)
    db.session.flush()
    if role == 'talent':
        user.talent_profile = TalentProfile(
            full_name='Test Talent',
            verification_status='unverified',
        )
    elif role == 'employer':
        user.employer_profile = EmployerProfile(
            business_name='Test Business',
        )
    db.session.commit()
    return user


def login(client, email):
    return client.post('/auth/login', data={
        'email': email,
        'password': 'StrongPass123',
    })


def test_email_verification_token_enables_account(app, client):
    from app.auth.verify_routes import build_token

    with app.app_context():
        user = create_user('talent', 'talent@example.com')
        token = build_token(user.email)
        user_id = user.id

    response = client.get(f'/auth/verify/{token}')
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, user_id).is_email_verified is True


def test_unverified_talent_cannot_apply_or_message(app, client):
    with app.app_context():
        talent_user = create_user('talent', 'talent@example.com')
        employer_user = create_user('employer', 'employer@example.com', verified=True)
        job = Job(
            employer_id=employer_user.employer_profile.id,
            title='Test role',
            description='A test role',
            category='Frontend Development',
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    login(client, talent_user.email)
    apply_response = client.post(f'/talent/jobs/{job_id}/apply')
    message_response = client.get('/messages/')

    assert apply_response.status_code == 302
    assert '/auth/verify' in apply_response.location
    assert message_response.status_code == 302
    assert '/auth/verify' in message_response.location
    with app.app_context():
        assert Application.query.count() == 0


def test_unverified_employer_cannot_post_or_checkout(app, client):
    with app.app_context():
        employer = create_user('employer', 'employer@example.com')

    login(client, employer.email)
    post_response = client.get('/employer/jobs/new')
    checkout_response = client.post(
        '/employer/billing/checkout',
        data={'plan': 'starter', 'provider': 'manual'},
    )

    assert post_response.status_code == 302
    assert '/auth/verify' in post_response.location
    assert checkout_response.status_code == 302
    assert '/auth/verify' in checkout_response.location
    with app.app_context():
        assert Job.query.count() == 0
        assert Payment.query.count() == 0


def test_talent_verification_request_is_reviewed_with_rationale(app, client):
    with app.app_context():
        talent = create_user('talent', 'talent@example.com', verified=True)
        talent_id = talent.talent_profile.id
        admin = create_user('admin', 'admin@example.com', verified=True)

    login(client, 'talent@example.com')
    request_response = client.post(
        '/talent/verification/request',
        data={'verification_note': 'My public profile is complete.'},
    )
    assert request_response.status_code == 302
    with app.app_context():
        profile = db.session.get(TalentProfile, talent_id)
        assert profile.verification_status == 'pending'
        assert profile.verification_request_note == 'My public profile is complete.'

    client.post('/auth/logout')
    login(client, admin.email)
    review_response = client.post(
        f'/admin/talent/{talent_id}/verify',
        data={'status': 'rejected', 'review_notes': 'Please add more profile detail.'},
    )
    assert review_response.status_code == 302
    with app.app_context():
        profile = db.session.get(TalentProfile, talent_id)
        assert profile.verification_status == 'rejected'
        assert profile.verification_review_notes == 'Please add more profile detail.'
        assert AuditLog.query.filter_by(
            action='talent_profile_verification_rejected',
        ).count() == 1


def test_employer_verification_request_can_be_approved(app, client):
    with app.app_context():
        employer = create_user('employer', 'employer@example.com', verified=True)
        profile_id = employer.employer_profile.id
        admin = create_user('admin', 'admin@example.com', verified=True)

    login(client, employer.email)
    request_response = client.post('/employer/verification/request')
    assert request_response.status_code == 302

    client.post('/auth/logout')
    login(client, admin.email)
    review_response = client.post(
        f'/admin/employers/{profile_id}/verify',
        data={'status': 'verified', 'review_notes': 'Business profile reviewed.'},
    )
    assert review_response.status_code == 302
    with app.app_context():
        profile = db.session.get(EmployerProfile, profile_id)
        assert profile.verification_status == 'verified'
        assert profile.verified is True
