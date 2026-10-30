from .extensions import db
from .utils.time import utcnow_naive


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow_naive, onupdate=utcnow_naive,
        nullable=False,
    )


class User(TimestampMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='talent', index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime)

    talent_profile = db.relationship(
        'TalentProfile', back_populates='user', uselist=False,
        cascade='all, delete-orphan',
    )
    employer_profile = db.relationship(
        'EmployerProfile', back_populates='user', uselist=False,
        cascade='all, delete-orphan',
    )
    notifications = db.relationship(
        'Notification', back_populates='user',
        cascade='all, delete-orphan', lazy='dynamic',
    )

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self):
        if self.talent_profile:
            return self.talent_profile.full_name or self.email
        if self.employer_profile:
            return self.employer_profile.business_name or self.email
        return self.email

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_admin(self):
        return self.role == 'admin'


job_skill = db.Table(
    'job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
)


talent_skill = db.Table(
    'talent_skills',
    db.Column('talent_id', db.Integer, db.ForeignKey('talent_profiles.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
)


class TalentProfile(TimestampMixin, db.Model):
    __tablename__ = 'talent_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False, default='')
    phone = db.Column(db.String(40))
    city = db.Column(db.String(100))
    bio = db.Column(db.Text)
    education = db.Column(db.String(255))
    experience_level = db.Column(db.String(30), default='Junior')
    expected_rate = db.Column(db.Numeric(12, 2))
    availability = db.Column(db.String(40), default='Available')
    portfolio_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    cv_filename = db.Column(db.String(255))
    avatar_filename = db.Column(db.String(255))
    verification_status = db.Column(db.String(30), default='unverified', index=True)
    trust_score = db.Column(db.Integer, default=0)
    headline = db.Column(db.String(180))

    user = db.relationship('User', back_populates='talent_profile')
    skills = db.relationship('Skill', secondary=talent_skill, back_populates='talents')
    applications = db.relationship(
        'Application', back_populates='talent', cascade='all, delete-orphan',
    )
    saved_jobs = db.relationship(
        'SavedJob', back_populates='talent', cascade='all, delete-orphan',
    )


class EmployerProfile(TimestampMixin, db.Model):
    __tablename__ = 'employer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    business_name = db.Column(db.String(180), nullable=False, default='')
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)
    city = db.Column(db.String(100))
    phone = db.Column(db.String(40))
    website = db.Column(db.String(500))
    registration_number = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False, nullable=False)
    logo_filename = db.Column(db.String(255))

    user = db.relationship('User', back_populates='employer_profile')
    jobs = db.relationship('Job', back_populates='employer', cascade='all, delete-orphan')


class Skill(TimestampMixin, db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    talents = db.relationship('TalentProfile', secondary=talent_skill, back_populates='skills')
    jobs = db.relationship('Job', secondary=job_skill, back_populates='skills')


class Job(TimestampMixin, db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profiles.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    engagement_type = db.Column(db.String(40), nullable=False, default='Apprenticeship')
    work_type = db.Column(db.String(40), nullable=False, default='Hybrid')
    city = db.Column(db.String(100))
    remote_allowed = db.Column(db.Boolean, default=False, nullable=False)
    salary_min = db.Column(db.Numeric(12, 2))
    salary_max = db.Column(db.Numeric(12, 2))
    duration_weeks = db.Column(db.Integer)
    status = db.Column(db.String(30), default='published', nullable=False, index=True)
    closing_date = db.Column(db.DateTime)
    views = db.Column(db.Integer, default=0, nullable=False)

    employer = db.relationship('EmployerProfile', back_populates='jobs')
    skills = db.relationship('Skill', secondary=job_skill, back_populates='jobs')
    applications = db.relationship('Application', back_populates='job', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', back_populates='job', cascade='all, delete-orphan')


class Application(TimestampMixin, db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    talent_id = db.Column(db.Integer, db.ForeignKey('talent_profiles.id'), nullable=False, index=True)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(30), default='submitted', nullable=False, index=True)
    employer_note = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)

    __table_args__ = (db.UniqueConstraint('job_id', 'talent_id', name='uq_application_job_talent'),)
    job = db.relationship('Job', back_populates='applications')
    talent = db.relationship('TalentProfile', back_populates='applications')
    apprenticeship = db.relationship(
        'Apprenticeship', back_populates='application', uselist=False,
        cascade='all, delete-orphan',
    )


class SavedJob(TimestampMixin, db.Model):
    __tablename__ = 'saved_jobs'
    id = db.Column(db.Integer, primary_key=True)
    talent_id = db.Column(db.Integer, db.ForeignKey('talent_profiles.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('talent_id', 'job_id', name='uq_saved_job'),)
    talent = db.relationship('TalentProfile', back_populates='saved_jobs')
    job = db.relationship('Job', back_populates='saved_by')


class Apprenticeship(TimestampMixin, db.Model):
    __tablename__ = 'apprenticeships'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), unique=True, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    allowance = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(30), default='proposed', nullable=False)
    objectives = db.Column(db.Text)
    supervisor_name = db.Column(db.String(160))
    supervisor_phone = db.Column(db.String(40))
    terms = db.Column(db.Text)
    completion_rating = db.Column(db.Integer)
    completion_note = db.Column(db.Text)

    application = db.relationship('Application', back_populates='apprenticeship')


class Notification(TimestampMixin, db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500))
    read_at = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='notifications')


class Message(TimestampMixin, db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    application = db.relationship('Application')


class Review(TimestampMixin, db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)


class Assessment(TimestampMixin, db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, default=30)
    pass_score = db.Column(db.Integer, default=70)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    questions = db.relationship('AssessmentQuestion', back_populates='assessment', cascade='all, delete-orphan')


class AssessmentQuestion(TimestampMixin, db.Model):
    __tablename__ = 'assessment_questions'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    choices = db.Column(db.Text, nullable=False)  # JSON list
    correct_index = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, default=1)
    assessment = db.relationship('Assessment', back_populates='questions')


class AssessmentAttempt(TimestampMixin, db.Model):
    __tablename__ = 'assessment_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)


class Payment(TimestampMixin, db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reference = db.Column(db.String(80), unique=True, nullable=False)
    provider = db.Column(db.String(40), nullable=False, default='manual')
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='XAF')
    purpose = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(30), default='pending', nullable=False)
    provider_reference = db.Column(db.String(160))
    metadata_json = db.Column(db.Text)


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80))
    entity_id = db.Column(db.String(80))
    metadata_json = db.Column(db.Text)


class ModerationReport(TimestampMixin, db.Model):
    __tablename__ = 'moderation_reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=False, index=True)
    reason = db.Column(db.String(40), nullable=False)
    details = db.Column(db.String(1000))
    status = db.Column(db.String(20), nullable=False, default='open', index=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.String(2000))

    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])
