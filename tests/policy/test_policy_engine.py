from src.policy.policy_engine import PolicyContext, enforce_policy


def test_policy_blocks_high_risk_without_approval():
    skills = [
        {"skill_id": "safe", "risk_level": "low"},
        {"skill_id": "high", "risk_level": "high"},
    ]
    allowed, blocked = enforce_policy(skills, PolicyContext())
    assert [s["skill_id"] for s in allowed] == ["safe"]
    assert blocked[0]["skill_id"] == "high"


def test_policy_allows_with_approval():
    skills = [{"skill_id": "high", "risk_level": "high"}]
    allowed, blocked = enforce_policy(skills, PolicyContext(approval_token="ok"))
    assert len(allowed) == 1
    assert blocked == []
