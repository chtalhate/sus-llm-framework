from __future__ import annotations

from app.domain.enums import HallucinationType


class TaxonomyClassifier:
    def classify(self, claim: str, supported: bool, has_sources: bool) -> list[str]:
        claim_l = claim.lower()
        tags: list[str] = []
        if not supported and any(x in claim_l for x in ['lei', 'portaria', 'decreto', 'pcdt', 'rename', 'sigtap']):
            tags.append(HallucinationType.T5.value)
        if not supported and any(x in claim_l for x in ['cobre', 'direito', 'garante', 'obrigatório']):
            tags.append(HallucinationType.T1.value)
        if not supported and any(x in claim_l for x in ['fila', 'regulação', 'sisreg', 'uti', 'encaminhamento', 'transfer']):
            tags.append(HallucinationType.T2.value)
        if not supported and any(x in claim_l for x in ['critério', 'elegível', 'tem direito', 'pré-requisito']):
            tags.append(HallucinationType.T3.value)
        if any(x in claim_l for x in ['deve tomar', 'ajuste a dose', 'indicação cirúrgica', 'internação psiquiátrica']):
            tags.append(HallucinationType.T4.value)
        if supported and not has_sources:
            tags.append(HallucinationType.T6.value)
        return sorted(set(tags))
