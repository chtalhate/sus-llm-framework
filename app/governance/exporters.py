from __future__ import annotations

import csv
from pathlib import Path
from app.governance.audit_logger import AuditLogger


class AuditExporter:
    def export_csv(self, output_path: str = 'data/processed/audit_export.csv') -> str:
        rows = AuditLogger().list_runs(limit=500)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            path.write_text('', encoding='utf-8')
            return str(path)
        with path.open('w', encoding='utf-8', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return str(path)
