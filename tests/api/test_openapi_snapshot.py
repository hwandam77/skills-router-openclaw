from src.api.app import app


def test_openapi_contains_required_routes():
    schema = app.openapi()
    paths = schema.get("paths", {})
    assert "/router/health" in paths
    assert "/router/plan" in paths
    assert "/router/execute" in paths
    assert "/router/runs/{run_id}" in paths
