from src.router.scoring_engine import rank_skills, score_skill


def test_score_skill_penalties_and_weights():
    skill = {"skill_id": "a", "status": "active", "risk_level": "low", "quality_score": 0.8}
    f = {
        "intent_match": 1.0,
        "vector_similarity": 0.5,
        "policy_fit": 1.0,
        "latency_fit": 1.0,
        "cost_fit": 1.0,
    }
    s = score_skill(skill, f)
    assert s > 0.7


def test_rank_skills_ordering():
    skills = [
        {"skill_id": "x", "status": "active", "risk_level": "low", "quality_score": 0.9},
        {"skill_id": "y", "status": "deprecated", "risk_level": "low", "quality_score": 0.9},
    ]
    feature_map = {
        "x": {"intent_match": 0.9, "vector_similarity": 0.8, "policy_fit": 1, "latency_fit": 1, "cost_fit": 1},
        "y": {"intent_match": 0.9, "vector_similarity": 0.8, "policy_fit": 1, "latency_fit": 1, "cost_fit": 1},
    }
    ranked = rank_skills(skills, feature_map)
    assert ranked[0]["skill_id"] == "x"
