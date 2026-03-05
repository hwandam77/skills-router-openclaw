from pathlib import Path
from src.router.shadow_runner import run_shadow_compare, write_shadow_diff_report


def test_shadow_runner_and_report(tmp_path: Path):
    skills = [
        {"skill_id": "a", "status": "active", "required_tools": [], "risk_level": "low"},
        {"skill_id": "b", "status": "active", "required_tools": ["exec"], "risk_level": "low"},
    ]
    result = run_shadow_compare(skills, ["read"], baseline_selected=["b"])
    report = tmp_path / "shadow.md"
    write_shadow_diff_report(report, result)
    assert report.exists()
