from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..models import Transaction
from ..schemas import TransactionIn, EvalResult
from ..engine.rules import evaluate

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/evaluate", response_model=EvalResult)
def evaluate_tx(tx: TransactionIn, db: Session = Depends(get_db),
                _=Depends(require_min("analyst"))):
    return evaluate(db, tx)


@router.get("")
def list_tx(limit: int = 25, db: Session = Depends(get_db),
            _=Depends(require_min("viewer"))):
    rows = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(limit).all()
    return [{
        "id": t.id, "account_id": t.account_id, "beneficiary": t.beneficiary,
        "amount": t.amount, "channel": t.channel, "score": t.score,
        "decision": t.decision, "fired": t.fired_rules or [],
        "created_at": t.created_at.isoformat(),
    } for t in rows]
