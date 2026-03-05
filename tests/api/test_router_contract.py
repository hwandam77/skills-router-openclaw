from fastapi.testclient import TestClient
from src.api.app import app


client = TestClient(app)


def test_health():
    r = client.get('/router/health')
    assert r.status_code == 200
    assert r.json()['ok'] is True


def test_plan_simple():
    payload = {
        'user_intent': 'debug production issue',
        'available_tools': ['read', 'exec'],
        'task_type': 'simple',
    }
    r = client.post('/router/plan', json=payload)
    assert r.status_code == 200
    body = r.json()
    assert 'run_id' in body
    assert isinstance(body['selected_skills'], list)


def test_execute_and_get_run():
    payload = {
        'user_intent': 'harden security',
        'available_tools': ['read', 'exec'],
        'task_type': 'composite',
        'approval_token': 'ok',
    }
    ex = client.post('/router/execute', json=payload)
    assert ex.status_code == 200
    rid = ex.json()['run_id']

    run = client.get(f'/router/runs/{rid}')
    assert run.status_code == 200
    assert run.json()['run_id'] == rid
