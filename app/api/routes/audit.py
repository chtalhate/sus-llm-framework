from fastapi import APIRouter
from app.governance.audit_logger import AuditLogger
from app.governance.exporters import AuditExporter

router = APIRouter(prefix='/audit', tags=['audit'])
logger = AuditLogger()
exporter = AuditExporter()


@router.get('')
def list_audit(limit: int = 50):
    return logger.list_runs(limit=limit)


@router.post('/export')
def export_audit():
    return {'path': exporter.export_csv()}
