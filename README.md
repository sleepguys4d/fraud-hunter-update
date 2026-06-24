# Fraud Hunter — Plataforma Antifraude (HIDEN Engine)

Versão especializada do **HIDEN** focada em fraude financeira: motor de regras a correr
a sério (com estado/histórico em base de dados), persistência via SQLAlchemy, RBAC,
mapeamento à **Fraud Kill Chain** com cobertura recalculada dinamicamente, e um console
web na identidade visual HUD.

Arquitetura de produto: **HIDEN** (CTI/IOCs) → **Fraud Hunter** (deteção/decisão) → **SOC Xpert** (gestão de casos).

> Plataforma **defensiva** (workbench de analista de fraude). Todos os dados de seed são
> fictícios e ilustrativos.

---

## Arrancar com Docker (recomendado para testar)

```bash
docker compose up --build
```

Depois abrir **http://localhost:8000** (frontend HUD · 10 separadores) e **http://localhost:8000/docs** (OpenAPI/Swagger).

A base de dados SQLite é persistida em `./data/fraud_hunter.db` (volume), pelo que os
dados sobrevivem a reinícios do contentor.

## Arrancar sem Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testes

```bash
pip install -r requirements.txt
pytest -q
```

10 testes cobrem o motor: aprovação limpa, beneficiário novo, aprendizagem de estado,
velocity, impossible travel, mula, estruturação, recálculo de cobertura e dashboard.

---

## Autenticação (RBAC)

Cabeçalho `X-API-Key`. Chaves de **desenvolvimento** semeadas:

| Papel    | Chave                 | Pode                                   |
|----------|-----------------------|----------------------------------------|
| admin    | `fh_admin_dev_key`    | tudo, incl. alterar/ligar/desligar regras |
| analyst  | `fh_analyst_dev_key`  | avaliar transações, criar casos        |
| viewer   | `fh_viewer_dev_key`   | apenas leitura                         |

Para testar sem autenticação, definir `AUTH_DISABLED=true`.
Em produção, substituir por sessão/OIDC (ex.: Keycloak, como no SOC Xpert).

---

## Motor de regras

Cada regra tem um **predicado real** avaliado sobre a transação + histórico da conta.
As regras ativas somam o peso ao *score* (0–100); o *score* determina a decisão.

Decisão: `≥80 BLOCK` · `60–79 REVIEW` · `35–59 CHALLENGE_3DS` · `<35 APPROVE`.

| Regra | Fase KC | Predicado |
|-------|---------|-----------|
| R-001 | 6 | velocity (>3 tx/10 min) |
| R-002 | 6 | beneficiário novo + montante atípico |
| R-003 | 5 | alteração de IBAN/contacto < 24h antes do pagamento |
| R-004 | 4 | impossible travel (geovelocity) |
| R-005 | 4 | dispositivo desconhecido |
| R-006 | 4 | biometria comportamental anómala |
| R-007 | 5 | SIM swap |
| R-008 | 8 | estruturação / smurfing |
| R-009 | 7 | conta-mula (receção→reenvio <1h) |
| R-010 | 8 | fundos circulares |
| R-011 | 2 | domínio lookalike (threat intel) |
| R-012 | 1 | credenciais corporativas vazadas |
| R-013 | 4 | geografia de risco (desligada por omissão) |
| R-014 | 6 | pagamento sem SCA / 3DS |

**Estado/aprendizagem:** quando uma transação não é bloqueada, a conta "aprende" o
beneficiário e o dispositivo — a mesma transação repetida deixa de disparar R-002/R-005.

---

## API (principais endpoints)

| Método | Rota | Papel mín. | Descrição |
|--------|------|------------|-----------|
| GET  | `/api/health` | — | estado do serviço |
| GET  | `/api/dashboard` | viewer | KPIs derivados da BD |
| GET  | `/api/killchain` | viewer | cobertura por fase |
| GET  | `/api/rules` | viewer | biblioteca de regras |
| PATCH| `/api/rules/{id}/toggle` | admin | ligar/desligar regra |
| PATCH| `/api/rules/{id}` | admin | ajustar peso/params |
| POST | `/api/transactions/evaluate` | analyst | **avaliar transação (motor)** |
| GET  | `/api/transactions` | viewer | transações persistidas |
| GET/POST | `/api/cases` | viewer / analyst | casos (ACFE Fraud Tree) |
| GET  | `/api/aml` | viewer | alertas AML/CFT |
| GET  | `/api/network` | viewer | grafo de mulas |
| GET  | `/api/threat` | viewer | exposição (domínios, fugas, marca) |

### Exemplo — avaliar uma transação

```bash
curl -s -X POST http://localhost:8000/api/transactions/evaluate \
  -H "X-API-Key: fh_admin_dev_key" -H "Content-Type: application/json" \
  -d '{
    "account_id": "AO-4471",
    "beneficiary": "AO-NEW-77",
    "amount": 4250000,
    "device_id": "dev-novo-99",
    "geo": "Lisboa", "lat": 38.72, "lng": -9.14,
    "behavior_score": 30,
    "sca_passed": false,
    "detail_changed": true
  }'
```

---

## Estrutura

```
fraud-hunter/
├── app/
│   ├── main.py            # FastAPI + lifespan (cria tabelas + seed)
│   ├── config.py          # settings (pydantic-settings)
│   ├── database.py        # engine + sessão SQLAlchemy
│   ├── clock.py           # relógio UTC
│   ├── models.py          # ORM
│   ├── schemas.py         # Pydantic
│   ├── auth.py            # RBAC por API key
│   ├── seed.py            # dados ilustrativos
│   ├── engine/
│   │   ├── rules.py       # motor + predicados reais
│   │   ├── killchain.py   # cobertura dinâmica
│   │   └── geo.py         # haversine / geovelocity
│   └── routers/           # dashboard, transactions, rules, killchain, cases, aml, network, threat
├── static/index.html      # frontend HUD de 10 separadores (consome a API ao vivo)
├── tests/test_engine.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Roteiro

Profiles GUI, gestão de membros RBAC, multitenancy (RLS), SSO/OIDC via Keycloak,
graph analytics nativo para o módulo de mulas e integração de webhooks com o SOC Xpert.
