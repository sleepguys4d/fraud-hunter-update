from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..models import NetworkNode, NetworkLink

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("")
def get_network(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    nodes = [{"id": n.id, "label": n.label, "type": n.ntype, "risk": n.risk}
             for n in db.query(NetworkNode).all()]
    links = [{"source": l.source, "target": l.target, "amount": l.amount}
             for l in db.query(NetworkLink).all()]
    return {"nodes": nodes, "links": links}
