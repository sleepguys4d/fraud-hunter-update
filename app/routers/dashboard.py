from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..clock import now_utc
from ..auth import require_min
from ..database import get_db
from ..models import Transaction, Case, AmlAlert
from ..engine.killchain import coverage

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    now = now_utc()
    d24 = now - timedelta(hours=24)
    txs = db.query(Transaction).filter(Transaction.created_at >= d24).all()
    analyzed = len(txs)
    blocked = [t for t in txs if t.decision == "BLOCK"]
    review = [t for t in txs if t.decision in ("REVIEW", "CHALLENGE_3DS")]
    alerts = [t for t in txs if t.decision != "APPROVE"]
    prevented = sum(t.amount for t in blocked)
    cov = coverage(db)["overall"]
    cases_active = db.query(Case).filter(Case.status == "active").count()
    aml_open = db.query(AmlAlert).count()
    fp = round(len(review) / analyzed * 100, 1) if analyzed else 0.0
    return {
        "cases_active": cases_active,
        "alerts_24h": len(alerts),
        "analyzed_24h": analyzed,
        "blocked_24h": len(blocked),
        "review_24h": len(review),
        "aml_open": aml_open,
        "prevented_amount": prevented,
        "coverage": cov,
        "fp_proxy": fp,
    }
