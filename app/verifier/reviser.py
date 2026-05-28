from __future__ import annotations

from app.core.constants import INSTITUTIONAL_WARNING
from app.domain.schemas import ClaimCheck


class Reviser:
    def revise(self, raw_answer: str, checks: list[ClaimCheck]) -> str:
        unsupported = [c for c in checks if not c.supported]
        if not unsupported:
            return raw_answer.strip() + "\n\n" + INSTITUTIONAL_WARNING

        revisions = ['Resposta revisada com verificação normativa:', raw_answer.strip(), '', 'Pontos de atenção identificados:']
        for item in unsupported[:5]:
            revisions.append(
                f"- '{item.claim}' -> revisar/confirmar em norma oficial; tipos detectados: {', '.join(item.taxonomy) or 'nenhum'}."
            )
        revisions.append('')
        revisions.append(INSTITUTIONAL_WARNING)
        return "\n".join(revisions)
