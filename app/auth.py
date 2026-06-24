from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

ROLE_RANK = {"viewer": 1, "analyst": 2, "admin": 3}


def _synthetic_admin() -> User:
    u = User(id="dev", name="Dev (auth desligada)", role="admin", api_key="dev")
    return u


def current_user(x_api_key: str | None = Header(default=None, alias="X-API-Key"),
                 db: Session = Depends(get_db)) -> User:
    if settings.auth_disabled:
        return _synthetic_admin()
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Falta o cabeçalho X-API-Key.")
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="API key inválida.")
    return user


def require_min(min_role: str):
    def dep(user: User = Depends(current_user)) -> User:
        if settings.auth_disabled:
            return user
        if ROLE_RANK.get(user.role, 0) < ROLE_RANK[min_role]:
            raise HTTPException(status_code=403, detail=f"Requer papel '{min_role}' ou superior.")
        return user
    return dep
