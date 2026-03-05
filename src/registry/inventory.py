from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _parse_frontmatter(skill_text: str) -> Dict[str, str]:
    m = FRONTMATTER_RE.match(skill_text)
    if not m:
        return {}
    out: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def build_inventory(skills_root: Path) -> List[Dict]:
    inventory: List[Dict] = []
    for skill_md in skills_root.glob("*/SKILL.md"):
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        meta = _parse_frontmatter(text)
        skill_id = skill_md.parent.name
        inventory.append(
            {
                "skill_id": skill_id,
                "version": meta.get("version", "0.1.0"),
                "status": "active",
                "domain": "general",
                "intents": [],
                "risk_level": "low",
                "required_tools": [],
                "latency_class": "normal",
                "cost_class": "normal",
                "conflicts": [],
                "dependencies": [],
                "quality_score": 0.5,
                "source_path": str(skill_md),
            }
        )
    return sorted(inventory, key=lambda x: x["skill_id"])


def write_inventory(skills_root: Path, output_path: Path) -> int:
    items = build_inventory(skills_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    root = Path("/home/hwandam/.openclaw/workspace/skills")
    out = Path("data/skill_inventory.json")
    count = write_inventory(root, out)
    print(f"wrote {count} skills -> {out}")
