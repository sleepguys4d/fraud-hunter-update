from typing import Optional
from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    account_id: str
    beneficiary: Optional[str] = None
    amount: float = 0.0
    channel: Optional[str] = "Transf. instantânea"
    direction: str = "out"  # out | in
    geo: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    device_id: Optional[str] = None
    behavior_score: Optional[int] = None
    sca_passed: bool = True
    detail_changed: bool = False  # simula alteração de IBAN/contacto antes da transação


class FiredRule(BaseModel):
    id: str
    name: str
    stage: int
    weight: int


class EvalResult(BaseModel):
    transaction_id: str
    account_id: str
    amount: float
    score: int
    decision: str
    fired: list[FiredRule]
    reason: str


class RuleUpdate(BaseModel):
    enabled: Optional[bool] = None
    severity: Optional[int] = None
    params: Optional[dict] = None


class CaseIn(BaseModel):
    title: str
    classification: str
    lifecycle: str = "Deteção"
    severity: str = "med"
    owner: Optional[str] = None
    linked: Optional[str] = None
