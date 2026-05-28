from __future__ import annotations

import uuid
from fastapi import APIRouter
from app.core.constants import INSTITUTIONAL_WARNING
from app.core.config import settings
from app.domain.schemas import AskRequest, AskResponse
from app.rag.retriever import LocalRetriever
from app.rag.reranker import SimpleReranker
from app.llm.generation import GeneratorService
from app.verifier.claim_extractor import ClaimExtractor
from app.verifier.evidence_checker import EvidenceChecker
from app.verifier.reviser import Reviser
from app.metrics.formulas import MetricsCalculator
from app.governance.audit_logger import AuditLogger

router = APIRouter(prefix='/ask', tags=['ask'])
retriever = LocalRetriever()
reranker = SimpleReranker()
generator = GeneratorService()
extractor = ClaimExtractor()
checker = EvidenceChecker()
reviser = Reviser()
metrics_calc = MetricsCalculator()
audit = AuditLogger()


@router.post('', response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    session_id = uuid.uuid4().hex[:12]
    trace = [{'stage': 'E1', 'description': 'Pergunta recebida', 'question': request.question}]

    chunks = []
    if request.condition.value in ('C2', 'C3'):
        chunks = retriever.search(request.question, top_k=min(request.top_k, settings.top_k))
        chunks = reranker.rerank(request.question, chunks, top_k=settings.rerank_k)
        trace.append({'stage': 'E2', 'description': 'Recuperação normativa', 'chunks': [c.chunk_id for c in chunks]})

    context = [f"{c.metadata.title}: {c.text}" for c in chunks[: settings.max_context_chunks]]
    raw_answer, llm_ok = generator.generate(request.question, request.condition.value, context)
    trace.append({'stage': 'E3', 'description': 'Geração', 'llm_ok': llm_ok})

    claims = extractor.extract(raw_answer)
    if request.condition.value == 'C3':
        checks = checker.check_claims(claims, chunks)
    else:
        checks = checker.check_claims(claims, chunks[:1])
    trace.append({'stage': 'E4', 'description': 'Verificação', 'claims': len(checks)})

    if request.condition.value == 'C3':
        answer = reviser.revise(raw_answer, checks)
    else:
        answer = raw_answer + "\n\n" + INSTITUTIONAL_WARNING

    metrics = metrics_calc.calculate(checks, len(chunks))
    trace.append({'stage': 'E5', 'description': 'Entrega', 'warning': True})

    payload = {
        'session_id': session_id,
        'question': request.question,
        'condition': request.condition.value,
        'answer': answer,
        'raw_answer': raw_answer,
        'claims': [c.model_dump() for c in checks],
        'retrieved_chunks': [c.model_dump() for c in chunks],
        'trace': trace + [{'stage': 'E6', 'description': 'Registro'}],
        'metrics': metrics.model_dump(),
    }
    audit_id = audit.save(payload)

    return AskResponse(
        session_id=session_id,
        question=request.question,
        condition=request.condition,
        answer=answer,
        raw_answer=raw_answer,
        warning=INSTITUTIONAL_WARNING,
        retrieved_chunks=chunks,
        claims=checks,
        metrics=metrics,
        audit_id=audit_id,
        trace=payload['trace'],
    )
