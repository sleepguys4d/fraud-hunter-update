from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from ..auth import require_min
from ..database import get_db
from ..models import Case
from ..schemas import CaseIn

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _ser(c: Case) -> dict:
    return {"id": c.id, "title": c.title, "classification": c.classification,
            "lifecycle": c.lifecycle, "severity": c.severity, "owner": c.owner,
            "linked": c.linked, "status": c.status}


@router.get("")
def list_cases(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    return [_ser(c) for c in db.query(Case).order_by(Case.id.desc()).all()]


@router.post("")
def create_case(body: CaseIn, db: Session = Depends(get_db),
                _=Depends(require_min("analyst"))):
    cid = "FH-2026-" + uuid.uuid4().hex[:4].upper()
    c = Case(id=cid, title=body.title, classification=body.classification,
             lifecycle=body.lifecycle, severity=body.severity,
             owner=body.owner, linked=body.linked)
    db.add(c)
    db.commit()
    return _ser(c)
