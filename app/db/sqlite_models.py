from sqlalchemy import Column, Integer, String, Text, Float
from app.db.session import Base


class AuditRun(Base):
    __tablename__ = 'audit_runs'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    question = Column(Text, nullable=False)
    condition = Column(String(8), nullable=False)
    answer = Column(Text, nullable=False)
    raw_answer = Column(Text, nullable=False)
    claims_json = Column(Text, nullable=False)
    retrieved_json = Column(Text, nullable=False)
    trace_json = Column(Text, nullable=False)
    ta = Column(Float, nullable=False)
    an = Column(Float, nullable=False)
    sm = Column(Float, nullable=False)
    f1 = Column(Float, nullable=False)
    ig = Column(Float, nullable=False)
    created_at = Column(String(32), nullable=False)
