from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .clock import now_utc

from .models import (User, Account, Transaction, Rule, Case, AmlAlert,
                     NetworkNode, NetworkLink, ThreatItem)

USERS = [
    ("u-admin", "S. Ajayi", "admin", "fh_admin_dev_key"),
    ("u-analyst", "A. Bula", "analyst", "fh_analyst_dev_key"),
    ("u-viewer", "P. Samuel", "viewer", "fh_viewer_dev_key"),
]

RULES = [
    ("R-001", "Velocity: >3 transferências em 10 min", 6, "Velocity", 22, True, "velocity_high", {"max": 3}),
    ("R-002", "Beneficiário novo + montante atípico", 6, "Comportamental", 28, True, "new_beneficiary", {"min_amount": 1000000}),
    ("R-003", "Alteração de IBAN seguida de pagamento <24h", 5, "Change-of-detail", 40, True, "iban_change_recent", {"hours": 24}),
    ("R-004", "Impossible travel no login", 4, "Geovelocity", 30, True, "impossible_travel", {"speed_kmh": 900}),
    ("R-005", "Dispositivo desconhecido em conta antiga", 4, "Device", 16, True, "unknown_device", {}),
    ("R-006", "Biometria comportamental anómala", 4, "Behavioral", 26, True, "behavioral_anomaly", {"min": 40}),
    ("R-007", "SIM swap detetado", 5, "Change-of-detail", 42, True, "sim_swap", {}),
    ("R-008", "Estruturação / smurfing (limiar repetido)", 8, "AML", 30, True, "structuring", {"threshold": 500000, "band": 0.85, "count": 3}),
    ("R-009", "Conta-mula: receção e reenvio <1h", 7, "Mule", 40, True, "mule_pattern", {"forward_ratio": 0.7}),
    ("R-010", "Padrão circular de fundos", 8, "Graph", 28, True, "circular_funds", {}),
    ("R-011", "Domínio lookalike registado", 2, "Brand", 14, True, "lookalike_domain", {}),
    ("R-012", "Credenciais corporativas vazadas", 1, "Threat Intel", 16, True, "leaked_credentials", {}),
    ("R-013", "Acesso de geografia de risco", 4, "Geo", 14, False, "risky_geo", {"list": ["Coreia do Norte", "Geo-risco"]}),
    ("R-014", "Pagamento sem SCA / 3DS falhado", 6, "Auth", 22, True, "missing_sca", {"min": 200000}),
]

ACCOUNTS = [
    ("AO-4471", ["dev-known-01"], ["AO-1180", "AO-9001"], "Luanda", -8.84, 13.23, False, True, False),
    ("AO-3302", ["dev-ios-9"], ["AO-0098"], "Luanda", -8.84, 13.23, False, False, False),
    ("AO-9920", [], [], "Luanda", -8.84, 13.23, False, False, True),
    ("AO-1180", ["dev-bg-2"], ["AO-5512"], "Benguela", -12.58, 13.41, False, False, False),
]

CASES = [
    ("FH-2026-118", "Rede de mulas — anel Kalandula", "Fraude externa · Mule ring", "Investigação", "crit", "S. Ajayi", "SOC-4471"),
    ("FH-2026-115", "ATO em conta empresarial", "Apropriação indevida de ativos", "Mitigação", "high", "A. Bula", "SOC-4468"),
    ("FH-2026-112", "Fraude de IBAN em fatura", "Fraude externa · BEC", "Análise", "high", "S. Ajayi", "SOC-4460"),
    ("FH-2026-108", "Suspeita de conluio interno", "Corrupção · Conflito de interesses", "Investigação", "med", "P. Samuel", None),
    ("FH-2026-101", "Estruturação recorrente", "Branqueamento · Smurfing", "Persecução", "high", "S. Ajayi", "UIF-2026-77"),
]

AML = [
    ("AML-512", "AO-9920", "Estruturação (8x abaixo do limiar)", "Placement", 3960000, "STR em curso", "high"),
    ("AML-509", "AO-0098", "Layering circular (4 saltos)", "Layering", 5400000, "Em análise", "high"),
    ("AML-505", "AO-8810", "Reenvio mula <1h", "Layering", 2100000, "Escalado", "crit"),
    ("AML-498", "AO-2231", "Integração via imóvel", "Integration", 12000000, "STR submetida", "crit"),
    ("AML-491", "AO-5512", "Cripto após receção", "Layering", 1800000, "Em análise", "med"),
]

NODES = [
    ("V1", "Vítima A", "victim", 30), ("V2", "Vítima B", "victim", 30), ("V3", "Vítima C", "victim", 30),
    ("M1", "Mula 1", "mule", 85), ("M2", "Mula 2", "mule", 88), ("M3", "Mula 3", "mule", 72), ("M4", "Mula 4", "mule", 90),
    ("C1", "Coletor", "collector", 95), ("X1", "Cash-out cripto", "cashout", 97), ("X2", "Cash-out ATM", "cashout", 80),
]
LINKS = [
    ("V1", "M1", 1500000), ("V2", "M2", 2100000), ("V3", "M2", 900000), ("M1", "C1", 1400000),
    ("M2", "C1", 2800000), ("M3", "C1", 600000), ("C1", "M4", 3200000), ("M4", "X1", 2900000),
    ("C1", "X2", 1100000), ("M2", "M3", 700000),
]

THREAT = [
    ("domain", "login-bancoatlantico.co", "Typosquat", "crit", "ativo", "há 5 dias"),
    ("domain", "kixipay-verificar.net", "Phishing ativo", "crit", "ativo", "há 1 dia"),
    ("domain", "fraud-hunter-secure.com", "Lookalike", "high", "monitorização", "há 2 dias"),
    ("leak", "Stealer log — 3 colaboradores", "Credenciais", "high", "rotação pedida", "há 3 dias"),
    ("leak", "Combo fórum — 12 e-mails @sec4data.ao", "E-mails", "med", "monitorização", "há 6 dias"),
    ("brand", "Perfil falso · rede social", None, "med", "Takedown pedido", "há 1 dia"),
]


def seed(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    for uid, name, role, key in USERS:
        db.add(User(id=uid, name=name, role=role, api_key=key))

    for rid, name, stage, rtype, sev, on, pred, params in RULES:
        db.add(Rule(id=rid, name=name, stage=stage, rtype=rtype, severity=sev,
                    enabled=on, predicate=pred, params=params))

    for aid, dev, ben, geo, lat, lng, sim, leak, pep in ACCOUNTS:
        db.add(Account(id=aid, known_devices=dev, seen_beneficiaries=ben, last_geo=geo,
                       last_lat=lat, last_lng=lng, last_seen_at=now_utc() - timedelta(hours=6),
                       sim_swap_flag=sim, cred_leak_flag=leak, is_pep=pep))

    for cid, title, cls, life, sev, owner, linked in CASES:
        db.add(Case(id=cid, title=title, classification=cls, lifecycle=life,
                    severity=sev, owner=owner, linked=linked))

    for aid, acc, pat, stage, amt, status, sev in AML:
        db.add(AmlAlert(id=aid, account_id=acc, pattern=pat, stage=stage,
                        amount=amt, status=status, severity=sev))

    for nid, label, ntype, risk in NODES:
        db.add(NetworkNode(id=nid, label=label, ntype=ntype, risk=risk))
    for src, tgt, amt in LINKS:
        db.add(NetworkLink(source=src, target=tgt, amount=amt))

    for kind, val, itype, risk, status, first in THREAT:
        db.add(ThreatItem(kind=kind, value=val, itype=itype, risk=risk, status=status, first_seen=first))

    db.commit()

    # histórico ilustrativo de transações (já avaliadas) para alimentar KPIs
    now = now_utc()
    history = [
        ("AO-1180", "AO-5512", 185000, "Pagamento POS", 18, "APPROVE", 30),
        ("AO-3302", "AO-0098", 990000, "Transf. interbancária", 67, "REVIEW", 90),
        ("AO-4471", "AO-8810", 4250000, "Transf. instantânea", 92, "BLOCK", 120),
        ("AO-9001", "AO-9001c", 320000, "Carregamento", 12, "APPROVE", 180),
        ("AO-6650", "AO-2231", 67500, "Pagamento online", 41, "CHALLENGE_3DS", 240),
    ]
    import uuid
    for acc, ben, amt, ch, score, dec, mins in history:
        db.add(Transaction(id="TX-" + uuid.uuid4().hex[:6].upper(), account_id=acc,
                            beneficiary=ben, amount=amt, channel=ch, direction="out",
                            created_at=now - timedelta(minutes=mins), score=score,
                            decision=dec, fired_rules=[]))
    db.commit()
