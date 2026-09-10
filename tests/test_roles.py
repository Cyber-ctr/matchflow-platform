from app.extensions import db
from app.models import User


def test_talent_cannot_open_employer_dashboard(client, app):
    with app.app_context():
        user = User(email='t@example.com', role='talent')
        user.set_password('StrongPass123')
        db.session.add(user)
        db.session.commit()
    client.post('/auth/login', data={'email': 't@example.com', 'password': 'StrongPass123'})
    response = client.get('/employer/dashboard')
    assert response.status_code == 403
