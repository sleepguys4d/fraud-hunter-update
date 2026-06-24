from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .clock import now_utc
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # admin | analyst | viewer
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    known_devices: Mapped[list] = mapped_column(JSON, default=list)
    seen_beneficiaries: Mapped[list] = mapped_column(JSON, default=list)
    last_geo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_detail_change_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sim_swap_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    cred_leak_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pep: Mapped[bool] = mapped_column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), index=True)
    beneficiary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    channel: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    direction: Mapped[str] = mapped_column(String, default="out")  # out | in
    geo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    behavior_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sca_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    decision: Mapped[str] = mapped_column(String, default="APPROVE")
    fired_rules: Mapped[list] = mapped_column(JSON, default=list)


class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    stage: Mapped[int] = mapped_column(Integer)
    rtype: Mapped[str] = mapped_column(String)
    severity: Mapped[int] = mapped_column(Integer, default=10)  # peso em pontos
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    predicate: Mapped[str] = mapped_column(String)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    hits: Mapped[int] = mapped_column(Integer, default=0)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    classification: Mapped[str] = mapped_column(String)
    lifecycle: Mapped[str] = mapped_column(String, default="Deteção")
    severity: Mapped[str] = mapped_column(String, default="med")
    owner: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linked: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class AmlAlert(Base):
    __tablename__ = "aml_alerts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pattern: Mapped[str] = mapped_column(String)
    stage: Mapped[str] = mapped_column(String)  # Placement | Layering | Integration
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="Em análise")
    severity: Mapped[str] = mapped_column(String, default="med")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class NetworkNode(Base):
    __tablename__ = "net_nodes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String)
    ntype: Mapped[str] = mapped_column(String)  # victim | mule | collector | cashout
    risk: Mapped[int] = mapped_column(Integer, default=0)


class NetworkLink(Base):
    __tablename__ = "net_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float, default=0.0)


class ThreatItem(Base):
    __tablename__ = "threat_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String)  # domain | leak | brand
    value: Mapped[str] = mapped_column(String)
    itype: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    risk: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_seen: Mapped[Optional[str]] = mapped_column(String, nullable=True)
