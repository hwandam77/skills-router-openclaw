import time
from src.policy.approval import ApprovalTokenStore


def test_issue_validate_consume():
    s = ApprovalTokenStore()
    s.issue('t1', ttl_seconds=3)
    assert s.validate('t1')
    assert s.consume('t1')
    assert not s.validate('t1')


def test_expiry():
    s = ApprovalTokenStore()
    s.issue('t2', ttl_seconds=1)
    time.sleep(1.1)
    assert not s.validate('t2')
