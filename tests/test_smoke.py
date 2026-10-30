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
    assert b'{else}' not in response.data
    assert b'Browse all opportunities' in response.data


def test_job_search_uses_labeled_responsive_filters(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert b'role="search"' in response.data
    assert b'Keywords' in response.data
    assert b'City' in response.data
    assert b'Clear filters' not in response.data
    assert b'Browse all opportunities' in response.data


def test_job_search_offers_to_clear_active_filters(client):
    response = client.get('/jobs?q=does-not-exist')
    assert response.status_code == 200
    assert b'Clear filters' in response.data


def test_footer_has_branded_navigation_sections(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert b'aria-label="MatchFlow home"' in response.data
    assert b'aria-label="Platform links"' in response.data
    assert b'aria-label="Legal links"' in response.data
    assert b'Building opportunity across Cameroon and Africa.' in response.data


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
