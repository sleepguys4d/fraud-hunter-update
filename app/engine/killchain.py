from sqlalchemy.orm import Session

from ..models import Rule

STAGES = {
    1: "Reconhecimento",
    2: "Preparação / Armamento",
    3: "Entrega / Contacto",
    4: "Comprometimento (ATO)",
    5: "Posicionamento",
    6: "Abuso / Execução",
    7: "Monetização",
    8: "Branqueamento",
}

# cobertura base para fases sem regra dedicada (controlos não-transacionais)
BASELINE = {1: 60, 2: 55, 3: 70, 4: 45, 5: 45, 6: 50, 7: 45, 8: 50}

TACTICS = {
    1: ["OSINT sobre o alvo", "Recolha de credenciais vazadas", "Perfilamento de PEPs"],
    2: ["Domínios typosquat", "Kits de phishing", "Contas-laranja pré-criadas"],
    3: ["Phishing / smishing / vishing", "Deepfake", "Engenharia social"],
    4: ["Roubo de credenciais", "RAT", "Login não autorizado"],
    5: ["Alteração de IBAN", "Novo dispositivo", "SIM swap"],
    6: ["Transferência fraudulenta", "Fraude de IBAN", "Compra de alto risco"],
    7: ["Reenvio via mulas", "Conversão cripto", "Levantamento numerário"],
    8: ["Placement", "Layering", "Integration", "Estruturação"],
}
CONTROLS = {
    1: ["Threat Intelligence (HIDEN)", "Monitorização de marca", "Vigilância de fugas"],
    2: ["Deteção de domínios novos", "Takedown", "Análise de infraestrutura"],
    3: ["DMARC/SPF/DKIM", "Anti-phishing", "Deteção de fraude em voz/SMS"],
    4: ["Device fingerprinting", "Biometria comportamental", "Impossible travel", "MFA forte"],
    5: ["Change-of-detail", "Cooling-off", "Deteção de SIM swap"],
    6: ["Monitorização em tempo real", "Scoring ML", "3DS / SCA"],
    7: ["Deteção de mulas", "Graph analytics", "Bloqueio de cash-out"],
    8: ["Monitorização AML/CFT", "Graph analytics", "Comunicação UIF (STR)"],
}


def coverage(db: Session) -> dict:
    rules = db.query(Rule).all()
    by_stage: dict[int, list[Rule]] = {s: [] for s in STAGES}
    for r in rules:
        by_stage.setdefault(r.stage, []).append(r)

    stages = []
    for s, name in STAGES.items():
        rs = by_stage.get(s, [])
        total = len(rs)
        active = sum(1 for r in rs if r.enabled)
        if total > 0:
            cov = round(50 + 45 * active / total)
        else:
            cov = BASELINE.get(s, 40)
        stages.append({
            "stage": s, "name": name, "coverage": cov,
            "active_rules": active, "total_rules": total,
            "rules": [r.id for r in rs],
            "tactics": TACTICS.get(s, []), "controls": CONTROLS.get(s, []),
        })
    overall = round(sum(x["coverage"] for x in stages) / len(stages))
    return {"overall": overall, "stages": stages}
