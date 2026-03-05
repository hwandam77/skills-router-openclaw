import json
from pathlib import Path
from src.obs.trace import append_trace


def test_append_trace(tmp_path: Path):
    log = tmp_path / "trace.jsonl"
    append_trace(log, {"run_id": "r1", "stage": "filter", "status": "success"})
    line = log.read_text().strip()
    data = json.loads(line)
    assert data["run_id"] == "r1"
    assert data["stage"] == "filter"
