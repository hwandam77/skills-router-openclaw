from src.registry.schema_validator import validate_skill


def test_validate_skill_ok():
    skill = {
        "skill_id": "x",
        "version": "1.0.0",
        "status": "active",
        "domain": "engineering",
        "intents": ["debug"],
        "risk_level": "low",
        "required_tools": ["read"],
        "latency_class": "normal",
        "cost_class": "low",
        "conflicts": [],
        "dependencies": [],
        "quality_score": 0.8,
    }
    ok, errors = validate_skill(skill)
    assert ok
    assert errors == []


def test_validate_skill_missing_and_enum():
    skill = {"skill_id": "x", "status": "bad"}
    ok, errors = validate_skill(skill)
    assert not ok
    assert any(e.startswith("missing:") for e in errors)
    assert "enum:status" in errors
