from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..models import ThreatItem

router = APIRouter(prefix="/api/threat", tags=["threat"])


@router.get("")
def list_threat(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    rows = db.query(ThreatItem).all()
    out = {"domain": [], "leak": [], "brand": []}
    for t in rows:
        out.setdefault(t.kind, []).append(
            {"value": t.value, "type": t.itype, "risk": t.risk,
             "status": t.status, "first_seen": t.first_seen})
    return out
