import json
import logging
from io import BytesIO

from sqlalchemy import inspect, text

from app.extensions import db
from app.models import (
    AuditLog, EmployerProfile, Job, ModerationReport, TalentProfile, User,
)
from app.services.observability import JsonLogFormatter


def create_user(email, role):
    user = User(email=email, role=role)
    user.set_password('StrongPass123')
    db.session.add(user)
    db.session.flush()
    if role == 'talent':
        db.session.add(TalentProfile(user_id=user.id, full_name=email.split('@')[0]))
    elif role == 'employer':
        db.session.add(EmployerProfile(user_id=user.id, business_name='Example Ltd', verified=True))
    db.session.flush()
    return user


def test_cv_and_avatar_use_local_storage_adapter(client, app, tmp_path):
    app.config['UPLOAD_FOLDER'] = str(tmp_path)
    with app.app_context():
        user = create_user('talent@example.com', 'talent')
        db.session.commit()
        user_id = user.id

    client.post('/auth/login', data={
        'email': 'talent@example.com',
        'password': 'StrongPass123',
    })
    assert client.get('/talent/profile').status_code == 200
    cv_response = client.post(
        '/talent/profile/cv',
        data={'cv': (BytesIO(b'%PDF-test'), 'resume.pdf')},
        content_type='multipart/form-data',
    )
    assert cv_response.status_code == 302
    with app.app_context():
        profile = TalentProfile.query.filter_by(user_id=user_id).one()
        assert profile.cv_filename.startswith('cvs/')
    assert client.get('/talent/profile/cv').data == b'%PDF-test'

    avatar_response = client.post(
        '/talent/profile/avatar',
        data={'avatar': (BytesIO(b'png-test'), 'photo.png')},
        content_type='multipart/form-data',
    )
    assert avatar_response.status_code == 302
    avatar = client.get(f'/talent/{user_id}/avatar')
    assert avatar.status_code == 200
    assert avatar.mimetype == 'image/png'
    assert avatar.data == b'png-test'


def test_job_report_is_triaged_and_audited(client, app):
    with app.app_context():
        reporter = create_user('reporter@example.com', 'talent')
        employer = create_user('employer@example.com', 'employer')
        admin = create_user('admin@example.com', 'admin')
        job = Job(
            employer_id=employer.employer_profile.id,
            title='Example job',
            description='Job description',
            category='Technology',
            engagement_type='Full-time',
            work_type='Remote',
        )
        db.session.add(job)
        db.session.commit()
        reporter_id = reporter.id
        job_id = job.id
        admin_email = admin.email

    client.post('/auth/login', data={
        'email': 'reporter@example.com',
        'password': 'StrongPass123',
    })
    response = client.post(
        f'/moderation/jobs/{job_id}',
        data={'reason': 'fraud', 'details': 'Requests payment to apply.'},
    )
    assert response.status_code == 302
    client.post(
        f'/moderation/jobs/{job_id}',
        data={'reason': 'spam', 'details': 'Duplicate submission.'},
    )
    with app.app_context():
        assert ModerationReport.query.filter_by(
            reporter_id=reporter_id, target_id=job_id,
        ).count() == 1

    admin_client = app.test_client()
    admin_client.post('/auth/login', data={
        'email': admin_email,
        'password': 'StrongPass123',
    })
    dashboard = admin_client.get('/admin/')
    assert dashboard.status_code == 200
    assert b'Open user reports' in dashboard.data
    with app.app_context():
        report = ModerationReport.query.filter_by(
            reporter_id=reporter_id, target_id=job_id,
        ).one()
        report_id = report.id
    reviewed = admin_client.post(
        f'/moderation/reports/{report_id}',
        data={'status': 'resolved', 'review_notes': 'Checked the listing and confirmed evidence of an advance-fee request.'},
    )
    assert reviewed.status_code == 302
    with app.app_context():
        report = db.session.get(ModerationReport, report_id)
        audit = AuditLog.query.filter_by(action='moderation_report_updated').one()
        assert report.status == 'resolved'
        assert report.reviewed_by_id is not None
        assert report.review_notes.startswith('Checked the listing')
        audit_details = json.loads(audit.metadata_json)
        assert audit_details['status'] == 'resolved'
        assert audit_details['review_notes'] == report.review_notes


def test_report_cannot_be_closed_without_review_notes(client, app):
    with app.app_context():
        reporter = create_user('review-reporter@example.com', 'talent')
        employer = create_user('review-employer@example.com', 'employer')
        admin = create_user('review-admin@example.com', 'admin')
        job = Job(
            employer_id=employer.employer_profile.id,
            title='Reviewable job',
            description='Job description',
            category='Technology',
            engagement_type='Full-time',
            work_type='Remote',
        )
        db.session.add(job)
        db.session.flush()
        report = ModerationReport(
            reporter_id=reporter.id,
            target_type='job',
            target_id=job.id,
            reason='fraud',
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id
        admin_email = admin.email

    client.post('/auth/login', data={
        'email': admin_email,
        'password': 'StrongPass123',
    })
    response = client.post(
        f'/moderation/reports/{report_id}',
        data={'status': 'dismissed'},
    )
    assert response.status_code == 302
    with app.app_context():
        report = db.session.get(ModerationReport, report_id)
        assert report.status == 'open'
        assert report.reviewed_by_id is None
        assert AuditLog.query.filter_by(action='moderation_report_updated').count() == 0


def test_json_logs_include_request_context(app):
    record = logging.LogRecord(
        'matchflow', logging.INFO, __file__, 1, 'operation complete', (), None,
    )
    with app.test_request_context('/health', method='GET'):
        from flask import g
        g.request_id = 'request-123'
        entry = json.loads(JsonLogFormatter().format(record))
    assert entry['request_id'] == 'request-123'
    assert entry['path'] == '/health'
    assert entry['message'] == 'operation complete'


def test_json_logs_redact_auth_tokens_from_paths(app):
    record = logging.LogRecord(
        'matchflow', logging.INFO, __file__, 1, 'request failed', (), None,
    )
    with app.test_request_context('/auth/reset-password/secret-token'):
        from flask import g
        g.request_id = 'request-456'
        entry = json.loads(JsonLogFormatter().format(record))
    assert entry['path'] == '/auth/reset-password/[redacted]'
    assert 'secret-token' not in json.dumps(entry)


def test_bootstrap_db_upgrades_existing_talent_profile_schema(app):
    with app.app_context():
        db.session.execute(text(
            'ALTER TABLE talent_profiles DROP COLUMN avatar_filename'
        ))
        db.session.commit()

    result = app.test_cli_runner().invoke(args=['bootstrap-db'])
    assert result.exit_code == 0
    with app.app_context():
        columns = {
            column['name']
            for column in inspect(db.engine).get_columns('talent_profiles')
        }
        assert 'avatar_filename' in columns
        assert 'moderation_reports' in inspect(db.engine).get_table_names()


def test_bootstrap_db_adds_review_notes_to_existing_report_table(app):
    with app.app_context():
        db.session.execute(text(
            'ALTER TABLE moderation_reports DROP COLUMN review_notes'
        ))
        db.session.commit()

    result = app.test_cli_runner().invoke(args=['bootstrap-db'])
    assert result.exit_code == 0
    with app.app_context():
        columns = {
            column['name']
            for column in inspect(db.engine).get_columns('moderation_reports')
        }
        assert 'review_notes' in columns


def test_s3_storage_uses_private_bucket_objects(app, monkeypatch):
    class FakeS3Client:
        def upload_fileobj(self, stream, bucket, key, ExtraArgs):
            self.upload = (stream.read(), bucket, key, ExtraArgs)

        def get_object(self, Bucket, Key):
            return {'Body': BytesIO(b'private object')}

    client = FakeS3Client()
    monkeypatch.setattr('boto3.client', lambda *args, **kwargs: client)
    app.config.update(
        OBJECT_STORAGE_BUCKET='private-bucket',
        OBJECT_STORAGE_PREFIX='uploads',
        OBJECT_STORAGE_REGION='auto',
    )
    with app.app_context():
        from app.services.storage import get_storage
        storage = get_storage()
        key = storage.save(BytesIO(b'cv-data'), 'cvs', 12, '.pdf', 'application/pdf')
        assert key.startswith('cvs/12/')
        assert client.upload[0] == b'cv-data'
        assert client.upload[1] == 'private-bucket'
        assert client.upload[2] == f'uploads/{key}'
        assert client.upload[3]['ContentType'] == 'application/pdf'
        assert storage.open(key).read() == b'private object'
