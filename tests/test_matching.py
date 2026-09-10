from app.models import Job, Skill, TalentProfile
from app.services.matching import job_match_score


def test_job_match_score(app):
    with app.app_context():
        html = Skill(name='HTML', category='Frontend Development')
        css = Skill(name='CSS', category='Frontend Development')
        talent = TalentProfile(user_id=1, full_name='Test')
        job = Job(employer_id=1, title='Test', description='Test', category='Frontend Development')
        talent.skills = [html, css]
        job.skills = [html, css]
        assert job_match_score(talent, job) == 100
