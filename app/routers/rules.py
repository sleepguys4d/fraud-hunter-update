from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..models import Rule
from ..schemas import RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["rules"])


def _sev_label(w: int) -> str:
    return "crit" if w >= 40 else "high" if w >= 24 else "med"


def _ser(r: Rule) -> dict:
    return {"id": r.id, "name": r.name, "stage": r.stage, "type": r.rtype,
            "weight": r.severity, "sev": _sev_label(r.severity), "enabled": r.enabled,
            "predicate": r.predicate, "params": r.params, "hits": r.hits}


@router.get("")
def list_rules(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    return [_ser(r) for r in db.query(Rule).order_by(Rule.id).all()]


@router.patch("/{rule_id}/toggle")
def toggle_rule(rule_id: str, db: Session = Depends(get_db),
                _=Depends(require_min("admin"))):
    r = db.get(Rule, rule_id)
    if not r:
        raise HTTPException(404, "Regra inexistente.")
    r.enabled = not r.enabled
    db.commit()
    return _ser(r)


@router.patch("/{rule_id}")
def update_rule(rule_id: str, body: RuleUpdate, db: Session = Depends(get_db),
                _=Depends(require_min("admin"))):
    r = db.get(Rule, rule_id)
    if not r:
        raise HTTPException(404, "Regra inexistente.")
    if body.enabled is not None:
        r.enabled = body.enabled
    if body.severity is not None:
        r.severity = body.severity
    if body.params is not None:
        r.params = body.params
    db.commit()
    return _ser(r)
