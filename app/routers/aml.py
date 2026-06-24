from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..models import AmlAlert

router = APIRouter(prefix="/api/aml", tags=["aml"])


@router.get("")
def list_aml(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    rows = db.query(AmlAlert).order_by(AmlAlert.id.desc()).all()
    return [{"id": a.id, "account_id": a.account_id, "pattern": a.pattern,
             "stage": a.stage, "amount": a.amount, "status": a.status,
             "severity": a.severity} for a in rows]
