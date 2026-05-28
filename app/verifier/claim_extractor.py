from __future__ import annotations

import re


class ClaimExtractor:
    def extract(self, answer: str) -> list[str]:
        parts = re.split(r'[\n\.!?;]+', answer)
        claims = []
        for part in parts:
            text = part.strip(' -•\t')
            if len(text) >= 20:
                claims.append(text)
        return claims[:8]
