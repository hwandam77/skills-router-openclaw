from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def append_trace(log_path: Path, record: Dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
