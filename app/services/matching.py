def job_match_score(talent, job):
    required = {skill.id for skill in job.skills}
    offered = {skill.id for skill in talent.skills}
    if not required:
        return 65
    overlap = len(required & offered) / len(required)
    score = round(overlap * 100)
    if talent.verification_status == 'verified':
        score = min(100, score + 5)
    return score


def recommended_jobs(talent, jobs, limit=6):
    ranked = [(job_match_score(talent, job), job) for job in jobs]
    ranked.sort(key=lambda item: (-item[0], item[1].created_at), reverse=False)
    return ranked[:limit]
