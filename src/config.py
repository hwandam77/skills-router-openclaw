from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = Path(os.getenv('SKILL_ROUTER_SKILLS_ROOT', '/home/hwandam/.openclaw/workspace/skills'))
REGISTRY_PATH = Path(os.getenv('SKILL_ROUTER_REGISTRY_PATH', str(ROOT / 'data' / 'skill_registry_v2.json')))
RUN_DB_PATH = Path(os.getenv('SKILL_ROUTER_RUN_DB', str(ROOT / 'data' / 'runs.sqlite3')))
