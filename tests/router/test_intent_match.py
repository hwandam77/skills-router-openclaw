from src.router.intent_match import compute_intent_match


def test_intent_match_prefers_related_skill():
    q = 'distributed queue retry dead letter'
    a = {'skill_id': 'redis-queue-worker', 'domain': 'backend', 'intents': ['queue', 'retry', 'dlq']}
    b = {'skill_id': 'ui-color-theme', 'domain': 'frontend', 'intents': ['theme', 'css']}
    assert compute_intent_match(q, a) > compute_intent_match(q, b)
