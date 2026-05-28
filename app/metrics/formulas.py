from __future__ import annotations

from app.domain.schemas import ClaimCheck, MetricsResult


class MetricsCalculator:
    def calculate(self, checks: list[ClaimCheck], retrieved_chunks_count: int) -> MetricsResult:
        total_claims = max(1, len(checks))
        supported = sum(1 for c in checks if c.supported)
        errors = [c for c in checks if not c.supported or c.taxonomy]
        hallucinated_responses = 1 if errors else 0
        ta = hallucinated_responses / 1
        an = supported / total_claims
        sm = (sum(c.severity for c in errors) / len(errors)) if errors else 0.0
        precision = an
        coverage = min(1.0, retrieved_chunks_count / max(1, total_claims))
        f1 = 0.0 if (precision + coverage) == 0 else (2 * (precision * coverage) / (precision + coverage))
        ig = (an + (1 - ta) + (1 - sm / 3)) / 3
        return MetricsResult(
            ta=round(ta, 4),
            an=round(an, 4),
            sm=round(sm, 4),
            f1=round(f1, 4),
            ig=round(ig, 4),
        )
