from __future__ import annotations

from app.db.repositories import AuditRepository


class AuditLogger:
    def __init__(self):
        self.repo = AuditRepository()

    def save(self, response_payload: dict) -> int:
        return self.repo.create(response_payload)

    def list_runs(self, limit: int = 50) -> list[dict]:
        return self.repo.list(limit=limit)
