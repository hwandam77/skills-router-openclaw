from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def append_filter_trace(log_path: Path, run_id: str, rejected: List[Dict]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for r in rejected:
            line = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "skill_id": r.get("skill_id"),
                "reason": r.get("reason"),
            }
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
