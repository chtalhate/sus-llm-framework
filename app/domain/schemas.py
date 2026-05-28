from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, List, Optional
from .enums import Condition


class ChunkMetadata(BaseModel):
    doc_id: str
    title: str
    source: str
    category: str
    section: str
    version: str = '1.0'


class NormChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    score: float = 0.0


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    condition: Condition = Condition.C3
    top_k: int = 6


class ClaimCheck(BaseModel):
    claim: str
    supported: bool
    evidence_chunk_ids: List[str] = Field(default_factory=list)
    evidence_titles: List[str] = Field(default_factory=list)
    notes: str = ''
    taxonomy: List[str] = Field(default_factory=list)
    severity: int = 0


class MetricsResult(BaseModel):
    ta: float
    an: float
    sm: float
    f1: float
    ig: float


class AskResponse(BaseModel):
    session_id: str
    question: str
    condition: Condition
    answer: str
    raw_answer: str
    warning: str
    retrieved_chunks: List[NormChunk]
    claims: List[ClaimCheck]
    metrics: MetricsResult
    audit_id: Optional[int] = None
    trace: List[dict[str, Any]] = Field(default_factory=list)


class BenchmarkItem(BaseModel):
    id: str
    axis: str
    question: str
    expected_keywords: List[str] = Field(default_factory=list)
    expected_sources: List[str] = Field(default_factory=list)
    risk_level: str = 'moderado'
    potential_types: List[str] = Field(default_factory=list)


class BenchmarkSummary(BaseModel):
    condition: Condition
    items: int
    avg_ta: float
    avg_an: float
    avg_sm: float
    avg_f1: float
    avg_ig: float
    details: List[dict[str, Any]]
