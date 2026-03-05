from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class RunStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def _init(self):
        with self._conn() as c:
            c.execute(
                '''
                CREATE TABLE IF NOT EXISTS runs (
                  run_id TEXT PRIMARY KEY,
                  status TEXT NOT NULL,
                  selected_skills TEXT NOT NULL,
                  rejected TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

    def upsert(self, run_id: str, status: str, selected_skills: list[str], rejected: list[dict]):
        with self._conn() as c:
            c.execute(
                '''
                INSERT INTO runs(run_id,status,selected_skills,rejected)
                VALUES(?,?,?,?)
                ON CONFLICT(run_id) DO UPDATE SET
                  status=excluded.status,
                  selected_skills=excluded.selected_skills,
                  rejected=excluded.rejected,
                  updated_at=CURRENT_TIMESTAMP
                ''',
                (run_id, status, json.dumps(selected_skills, ensure_ascii=False), json.dumps(rejected, ensure_ascii=False)),
            )

    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute('SELECT run_id,status,selected_skills,rejected FROM runs WHERE run_id=?', (run_id,)).fetchone()
            if not row:
                return None
            return {
                'run_id': row[0],
                'status': row[1],
                'selected_skills': json.loads(row[2]),
                'rejected': json.loads(row[3]),
            }
