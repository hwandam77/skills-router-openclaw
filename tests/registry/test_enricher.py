from src.registry.enricher import enrich_skills


def test_enricher_adds_defaults():
    skills = [{"skill_id": "x", "version": "1.0.0"}]
    out = enrich_skills(skills)
    assert out[0]["status"] == "active"
    assert out[0]["risk_level"] == "low"
    assert out[0]["quality_score"] == 0.5
