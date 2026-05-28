import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.sqlite_models import AuditRun


class AuditRepository:
    def create(self, payload: dict) -> int:
        with SessionLocal() as session:
            obj = AuditRun(
                session_id=payload['session_id'],
                question=payload['question'],
                condition=payload['condition'],
                answer=payload['answer'],
                raw_answer=payload['raw_answer'],
                claims_json=json.dumps(payload['claims'], ensure_ascii=False),
                retrieved_json=json.dumps(payload['retrieved_chunks'], ensure_ascii=False),
                trace_json=json.dumps(payload['trace'], ensure_ascii=False),
                ta=payload['metrics']['ta'],
                an=payload['metrics']['an'],
                sm=payload['metrics']['sm'],
                f1=payload['metrics']['f1'],
                ig=payload['metrics']['ig'],
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj.id

    def list(self, limit: int = 50) -> list[dict]:
        with SessionLocal() as session:
            rows = session.execute(select(AuditRun).order_by(AuditRun.id.desc()).limit(limit)).scalars().all()
            return [
                {
                    'id': row.id,
                    'session_id': row.session_id,
                    'question': row.question,
                    'condition': row.condition,
                    'ta': row.ta,
                    'an': row.an,
                    'sm': row.sm,
                    'f1': row.f1,
                    'ig': row.ig,
                    'created_at': row.created_at,
                }
                for row in rows
            ]
