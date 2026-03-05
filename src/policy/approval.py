from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class ApprovalTokenStore:
    tokens: dict[str, datetime] = field(default_factory=dict)
    consumed: set[str] = field(default_factory=set)

    def issue(self, token: str, ttl_seconds: int = 600) -> None:
        self.tokens[token] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    def validate(self, token: str) -> bool:
        if token in self.consumed:
            return False
        exp = self.tokens.get(token)
        if not exp:
            return False
        if datetime.now(timezone.utc) > exp:
            return False
        return True

    def consume(self, token: str) -> bool:
        if not self.validate(token):
            return False
        self.consumed.add(token)
        return True
