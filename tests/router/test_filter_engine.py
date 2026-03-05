from src.router.filter_engine import RouterContext, filter_candidates


def test_filter_candidates_rules():
    skills = [
        {"skill_id": "a", "status": "active", "required_tools": ["read"], "risk_level": "low"},
        {"skill_id": "b", "status": "deprecated", "required_tools": [], "risk_level": "low"},
        {"skill_id": "c", "status": "active", "required_tools": ["exec"], "risk_level": "low"},
        {"skill_id": "d", "status": "active", "required_tools": [], "risk_level": "high"},
    ]
    passed, rejected = filter_candidates(skills, RouterContext(available_tools=["read"]))
    assert [s["skill_id"] for s in passed] == ["a"]
    reasons = {r["skill_id"]: r["reason"] for r in rejected}
    assert reasons["b"] == "status_not_active"
    assert reasons["c"] == "missing_required_tools"
    assert reasons["d"] == "approval_required"
