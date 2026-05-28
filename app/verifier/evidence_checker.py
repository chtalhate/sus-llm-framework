from __future__ import annotations

from collections import Counter
from app.domain.schemas import ClaimCheck, NormChunk
from app.verifier.taxonomy import TaxonomyClassifier


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in text.replace('/', ' ').replace('-', ' ').split() if len(t) > 2]


class EvidenceChecker:
    def __init__(self):
        self.taxonomy = TaxonomyClassifier()

    def check_claims(self, claims: list[str], chunks: list[NormChunk]) -> list[ClaimCheck]:
        results: list[ClaimCheck] = []
        joined_chunks = {chunk.chunk_id: Counter(_tokenize(chunk.text + ' ' + chunk.metadata.title)) for chunk in chunks}
        for claim in claims:
            c_tokens = Counter(_tokenize(claim))
            scored: list[tuple[int, NormChunk]] = []
            for chunk in chunks:
                overlap = sum(min(c_tokens[t], joined_chunks[chunk.chunk_id][t]) for t in c_tokens)
                if overlap > 0:
                    scored.append((overlap, chunk))
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [chunk for _, chunk in scored[:2]]
            supported = bool(top and scored[0][0] >= 2)
            taxonomy = self.taxonomy.classify(claim, supported=supported, has_sources=bool(top))
            severity = min(3, max(0, len(taxonomy)))
            notes = 'Afirmação suportada por trechos recuperados.' if supported else 'Afirmação sem suporte robusto nos trechos recuperados.'
            results.append(
                ClaimCheck(
                    claim=claim,
                    supported=supported,
                    evidence_chunk_ids=[c.chunk_id for c in top],
                    evidence_titles=[c.metadata.title for c in top],
                    notes=notes,
                    taxonomy=taxonomy,
                    severity=severity,
                )
            )
        return results
