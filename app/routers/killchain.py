from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_min
from ..database import get_db
from ..engine.killchain import coverage

router = APIRouter(prefix="/api/killchain", tags=["killchain"])


@router.get("")
def get_killchain(db: Session = Depends(get_db), _=Depends(require_min("viewer"))):
    return coverage(db)
