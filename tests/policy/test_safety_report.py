from pathlib import Path
from src.policy.safety_report import write_safety_report


def test_write_safety_report(tmp_path: Path):
    out = tmp_path / 'safety.md'
    events = [
        {'skill_id': 'x', 'reason': 'policy_block:approval_required'},
        {'skill_id': 'y', 'reason': 'policy_block:approval_required'},
        {'skill_id': 'z', 'reason': 'policy_block:dangerous_action_requires_approval'},
    ]
    write_safety_report(out, events)
    text = out.read_text()
    assert 'total_blocked: 3' in text
