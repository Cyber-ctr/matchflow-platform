import click
from flask import current_app
from app.extensions import db
from app.models import Assessment, AssessmentQuestion, EmployerProfile, Skill, TalentProfile, User


SKILLS = [
    ('HTML', 'Frontend Development'), ('CSS', 'Frontend Development'),
    ('JavaScript', 'Frontend Development'), ('React', 'Frontend Development'),
    ('Git', 'Frontend Development'), ('Figma', 'Graphic Design'),
    ('Adobe Illustrator', 'Graphic Design'), ('Photoshop', 'Graphic Design'),
    ('Canva', 'Graphic Design'), ('Branding', 'Graphic Design'),
    ('Excel', 'Bookkeeping'), ('QuickBooks', 'Bookkeeping'),
    ('Reconciliation', 'Bookkeeping'), ('Invoicing', 'Bookkeeping'),
    ('Accounting', 'Bookkeeping'),
]


def register_commands(app):
    @app.cli.command('bootstrap-db')
    def bootstrap_db():
        """Create missing tables and safely add missing nullable model columns."""
        db.create_all()
        from sqlalchemy import inspect
        from sqlalchemy.schema import CreateColumn

        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        added_columns = []
        unsafe_columns = []
        with db.engine.begin() as connection:
            preparer = connection.dialect.identifier_preparer
            for table in db.metadata.sorted_tables:
                if table.name not in existing_tables:
                    continue
                existing_columns = {
                    column['name']
                    for column in inspector.get_columns(table.name, schema=table.schema)
                }
                for column in table.columns:
                    if column.name in existing_columns:
                        continue
                    if not column.nullable and column.server_default is None:
                        unsafe_columns.append(f'{table.name}.{column.name}')
                        continue
                    table_name = preparer.format_table(table)
                    column_ddl = str(
                        CreateColumn(column).compile(dialect=connection.dialect)
                    )
                    connection.exec_driver_sql(
                        f'ALTER TABLE {table_name} ADD COLUMN {column_ddl}'
                    )
                    added_columns.append(f'{table.name}.{column.name}')
            if 'employer_profiles' in existing_tables:
                connection.exec_driver_sql(
                    "UPDATE employer_profiles SET verification_status = 'verified' "
                    "WHERE verified = TRUE AND verification_status = 'unverified'"
                )
        if unsafe_columns:
            raise click.ClickException(
                'Existing database is missing required columns that cannot be '
                'added safely without data migration: '
                f'{", ".join(unsafe_columns)}. Create and review a Flask-Migrate '
                'migration, then run `flask --app wsgi:app db upgrade`.'
            )
        if added_columns:
            click.echo(f'Added missing nullable columns: {", ".join(added_columns)}.')
        existing = {skill.name for skill in Skill.query.all()}
        for name, category in SKILLS:
            if name not in existing:
                db.session.add(Skill(name=name, category=category))
        db.session.commit()
        click.echo('Database schema created and starter skills loaded.')

    @app.cli.command('create-admin')
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, password):
        """Create an administrator account."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise click.ClickException('That email already exists.')
        user = User(email=email, role='admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Administrator created.')

    @app.cli.command('seed-demo')
    @click.option('--force', is_flag=True, help='Replace demo data if it exists.')
    def seed_demo(force):
        """Seed clearly labelled demo users and sample opportunities."""
        from app.models import Job
        if force:
            for email in ('demo.talent@matchflow.local', 'demo.sme@matchflow.local'):
                old = User.query.filter_by(email=email).first()
                if old:
                    db.session.delete(old)
            db.session.commit()
        if User.query.filter_by(email='demo.talent@matchflow.local').first():
            click.echo('Demo data already exists.')
            return
        skills = {s.name: s for s in Skill.query.all()}
        talent_user = User(
            email='demo.talent@matchflow.local',
            role='talent',
            is_email_verified=True,
        )
        talent_user.set_password('DemoTalent@123')
        employer_user = User(
            email='demo.sme@matchflow.local',
            role='employer',
            is_email_verified=True,
        )
        employer_user.set_password('DemoEmployer@123')
        db.session.add_all([talent_user, employer_user])
        db.session.flush()
        talent = TalentProfile(
            user_id=talent_user.id, full_name='Demo Talent',
            headline='Junior Frontend Developer', city='Douala',
            bio='Demo profile for product testing.', trust_score=78,
            verification_status='verified',
        )
        talent.skills = [skills['HTML'], skills['CSS'], skills['JavaScript'], skills['Git']]
        employer = EmployerProfile(
            user_id=employer_user.id, business_name='Demo SME Cameroon',
            industry='Technology', city='Douala', verified=True,
            description='Demo employer profile for testing MatchFlow.',
        )
        db.session.add_all([talent, employer])
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            title='Junior Frontend Developer Apprentice',
            description='Build responsive interfaces, collaborate with a senior developer and ship a portfolio-ready client project.',
            category='Frontend Development', engagement_type='Apprenticeship',
            work_type='Hybrid', city='Douala', duration_weeks=12,
            salary_min=75000, salary_max=100000, status='published',
        )
        job.skills = [skills['HTML'], skills['CSS'], skills['JavaScript'], skills['Git']]
        db.session.add(job)
        db.session.commit()
        click.echo('Demo users and opportunity created.')

    @app.cli.command('seed-assessments')
    def seed_assessments():
        """Create starter skill assessments for the initial categories."""
        if Assessment.query.first():
            click.echo('Assessments already exist.')
            return
        import json
        banks = [
            (
                'Frontend Foundations', 'Frontend Development',
                [
                    ('What does CSS primarily control?', ['Database records', 'Page presentation', 'Server routing', 'Email delivery'], 1),
                    ('Which technology is primarily used to create page structure?', ['HTML', 'SQL', 'SMTP', 'Redis'], 0),
                    ('Which command creates a Git commit?', ['git push', 'git pull', 'git commit', 'git clone'], 2),
                ],
            ),
            (
                'Graphic Design Foundations', 'Graphic Design',
                [
                    ('Which format is generally best for an editable logo asset?', ['SVG', 'TXT', 'CSV', 'MP3'], 0),
                    ('What does typography primarily concern?', ['Type design and arrangement', 'Database security', 'Network routing', 'Payroll tax'], 0),
                    ('Which tool is commonly used for interface design?', ['Figma', 'PostgreSQL', 'Gunicorn', 'Redis'], 0),
                ],
            ),
            (
                'Bookkeeping Foundations', 'Bookkeeping',
                [
                    ('What is reconciliation?', ['Comparing records to confirm they agree', 'Designing a logo', 'Deploying a server', 'Writing CSS'], 0),
                    ('An invoice is primarily used to:', ['Request payment for goods or services', 'Store passwords', 'Create a website', 'Resize an image'], 0),
                    ('Which tool is widely used for spreadsheet-based bookkeeping?', ['Excel', 'Figma', 'Git', 'HTML'], 0),
                ],
            ),
        ]
        for name, category, questions in banks:
            assessment = Assessment(name=name, category=category, duration_minutes=20, pass_score=70)
            db.session.add(assessment)
            db.session.flush()
            for prompt, choices, correct in questions:
                db.session.add(AssessmentQuestion(
                    assessment_id=assessment.id,
                    prompt=prompt,
                    choices=json.dumps(choices),
                    correct_index=correct,
                ))
        db.session.commit()
        click.echo('Starter assessments created.')
