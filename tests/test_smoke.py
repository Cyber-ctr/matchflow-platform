from app.extensions import db
from app.models import Skill, User


def test_health(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'MatchFlow' in response.data


def test_register_login(client, app):
    response = client.post('/auth/register', data={
        'role': 'talent',
        'email': 'person@example.com',
        'password': 'StrongPass123',
        'confirm_password': 'StrongPass123',
        'full_name': 'Example Person',
    }, follow_redirects=False)
    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(email='person@example.com').first()
        assert user is not None
        assert user.talent_profile.full_name == 'Example Person'
