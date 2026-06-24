"""
Motor de regras do Fraud Hunter.

Cada predicado é uma função real avaliada sobre a transação em curso e o
contexto histórico da conta (consultado à base de dados). As regras ativas
somam o respetivo peso ao score; o score determina a decisão.
"""
from datetime import datetime, timedelta
from typing import Callable
import uuid

from sqlalchemy.orm import Session

from ..clock import now_utc
from ..config import settings
from ..models import Account, Transaction, Rule
from ..schemas import TransactionIn, EvalResult, FiredRule
from .geo import haversine_km, implied_speed_kmh

PREDICATES: dict[str, Callable] = {}


def predicate(key: str):
    def deco(fn: Callable):
        PREDICATES[key] = fn
        return fn
    return deco


# ----------------------------- predicados -----------------------------

@predicate("velocity_high")
def _velocity_high(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return len(ctx["recent_10m"]) >= int(p.get("max", 3))


@predicate("new_beneficiary")
def _new_beneficiary(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    if not tx.beneficiary:
        return False
    known = ctx["account"].seen_beneficiaries or []
    return tx.beneficiary not in known and tx.amount >= float(p.get("min_amount", 1_000_000))


@predicate("iban_change_recent")
def _iban_change_recent(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    acc = ctx["account"]
    changed = tx.detail_changed or bool(acc.last_detail_change_at and
              (ctx["now"] - acc.last_detail_change_at) < timedelta(hours=int(p.get("hours", 24))))
    return changed and tx.direction == "out" and tx.amount > 0


@predicate("impossible_travel")
def _impossible_travel(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    acc = ctx["account"]
    if None in (acc.last_lat, acc.last_lng, tx.lat, tx.lng) or not acc.last_seen_at:
        return False
    km = haversine_km(acc.last_lat, acc.last_lng, tx.lat, tx.lng)
    if km < 50:
        return False
    secs = max((ctx["now"] - acc.last_seen_at).total_seconds(), 1.0)
    return implied_speed_kmh(km, secs) > float(p.get("speed_kmh", 900))


@predicate("unknown_device")
def _unknown_device(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    if not tx.device_id:
        return False
    return tx.device_id not in (ctx["account"].known_devices or [])


@predicate("behavioral_anomaly")
def _behavioral_anomaly(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return tx.behavior_score is not None and tx.behavior_score < int(p.get("min", 40))


@predicate("sim_swap")
def _sim_swap(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return bool(ctx["account"].sim_swap_flag)


@predicate("structuring")
def _structuring(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    th = float(p.get("threshold", 500_000))
    band = float(p.get("band", 0.85))
    need = int(p.get("count", 3))
    lo, hi = th * band, th
    near = [t for t in ctx["recent_24h"] if lo <= t.amount < hi]
    if lo <= tx.amount < hi:
        near.append(tx)
    return len(near) >= need


@predicate("mule_pattern")
def _mule_pattern(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    if tx.direction != "out":
        return False
    inbound = sum(t.amount for t in ctx["inbound_1h"])
    return inbound > 0 and tx.amount >= float(p.get("forward_ratio", 0.7)) * inbound


@predicate("circular_funds")
def _circular_funds(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    # fundos que regressam: o beneficiário já enviou para esta conta nas últimas 24h
    if not tx.beneficiary:
        return False
    db: Session = ctx["db"]
    since = ctx["now"] - timedelta(hours=24)
    back = db.query(Transaction).filter(
        Transaction.account_id == tx.beneficiary,
        Transaction.beneficiary == tx.account_id,
        Transaction.created_at >= since,
    ).first()
    return back is not None


@predicate("leaked_credentials")
def _leaked_credentials(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return bool(ctx["account"].cred_leak_flag)


@predicate("missing_sca")
def _missing_sca(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return (not tx.sca_passed) and tx.amount >= float(p.get("min", 200_000))


@predicate("risky_geo")
def _risky_geo(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    return tx.geo in (p.get("list") or [])


@predicate("lookalike_domain")
def _lookalike_domain(tx: TransactionIn, ctx: dict, p: dict) -> bool:
    # acionado por threat intelligence, não pela transação
    return False


# ----------------------------- decisão -----------------------------

def decide(score: int) -> str:
    if score >= settings.t_block:
        return "BLOCK"
    if score >= settings.t_review:
        return "REVIEW"
    if score >= settings.t_challenge:
        return "CHALLENGE_3DS"
    return "APPROVE"


DECISION_PT = {
    "BLOCK": "Bloqueado",
    "REVIEW": "Enviado para revisão",
    "CHALLENGE_3DS": "Desafio 3DS / SCA",
    "APPROVE": "Aprovado",
}


def _get_or_create_account(db: Session, account_id: str) -> Account:
    acc = db.get(Account, account_id)
    if acc is None:
        acc = Account(id=account_id, known_devices=[], seen_beneficiaries=[])
        db.add(acc)
        db.flush()
    return acc


def evaluate(db: Session, tx_in: TransactionIn) -> EvalResult:
    now = now_utc()
    acc = _get_or_create_account(db, tx_in.account_id)

    recent_10m = db.query(Transaction).filter(
        Transaction.account_id == acc.id,
        Transaction.created_at >= now - timedelta(minutes=10),
    ).all()
    recent_24h = db.query(Transaction).filter(
        Transaction.account_id == acc.id,
        Transaction.created_at >= now - timedelta(hours=24),
    ).all()
    inbound_1h = db.query(Transaction).filter(
        Transaction.account_id == acc.id,
        Transaction.direction == "in",
        Transaction.created_at >= now - timedelta(hours=1),
    ).all()

    ctx = {"account": acc, "now": now, "db": db,
           "recent_10m": recent_10m, "recent_24h": recent_24h, "inbound_1h": inbound_1h}

    rules = db.query(Rule).filter(Rule.enabled == True).all()  # noqa: E712
    score = 0
    fired: list[FiredRule] = []
    for r in rules:
        fn = PREDICATES.get(r.predicate)
        if fn is None:
            continue
        try:
            hit = fn(tx_in, ctx, r.params or {})
        except Exception:
            hit = False
        if hit:
            score += r.severity
            r.hits += 1
            fired.append(FiredRule(id=r.id, name=r.name, stage=r.stage, weight=r.severity))

    score = min(score, 100)
    decision = decide(score)

    txid = "TX-" + uuid.uuid4().hex[:6].upper()
    rec = Transaction(
        id=txid, account_id=acc.id, beneficiary=tx_in.beneficiary, amount=tx_in.amount,
        channel=tx_in.channel, direction=tx_in.direction, geo=tx_in.geo, lat=tx_in.lat,
        lng=tx_in.lng, device_id=tx_in.device_id, behavior_score=tx_in.behavior_score,
        sca_passed=tx_in.sca_passed, created_at=now, score=score, decision=decision,
        fired_rules=[f.id for f in fired],
    )
    db.add(rec)

    # aprendizagem de estado: só "confia" quando não é bloqueado
    if decision != "BLOCK":
        if tx_in.beneficiary and tx_in.beneficiary not in (acc.seen_beneficiaries or []):
            acc.seen_beneficiaries = list(acc.seen_beneficiaries or []) + [tx_in.beneficiary]
        if tx_in.device_id and tx_in.device_id not in (acc.known_devices or []):
            acc.known_devices = list(acc.known_devices or []) + [tx_in.device_id]
    if tx_in.detail_changed:
        acc.last_detail_change_at = now
    if tx_in.geo:
        acc.last_geo = tx_in.geo
    if tx_in.lat is not None and tx_in.lng is not None:
        acc.last_lat, acc.last_lng = tx_in.lat, tx_in.lng
    acc.last_seen_at = now

    db.commit()

    reason = (f"{len(fired)} regra(s) acionada(s) · "
              f"score {score}/100 → {DECISION_PT[decision]}") if fired else \
             f"Sem sinais de risco · score 0/100 → {DECISION_PT[decision]}"

    return EvalResult(transaction_id=txid, account_id=acc.id, amount=tx_in.amount,
                      score=score, decision=decision, fired=fired, reason=reason)
