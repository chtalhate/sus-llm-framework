from app.metrics.formulas import MetricsCalculator
from app.domain.schemas import ClaimCheck


def test_metrics_basic():
    metrics = MetricsCalculator().calculate(
        [
            ClaimCheck(claim='a', supported=True, evidence_chunk_ids=[], evidence_titles=[]),
            ClaimCheck(claim='b', supported=False, evidence_chunk_ids=[], evidence_titles=[], taxonomy=['T1'], severity=1),
        ],
        retrieved_chunks_count=2,
    )
    assert 0 <= metrics.ig <= 1
    assert metrics.ta == 1.0
