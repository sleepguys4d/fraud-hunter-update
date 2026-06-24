import os
import pathlib

# configura ambiente de teste ANTES de importar a app
TEST_DB = pathlib.Path(__file__).parent / "test_fh.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["AUTH_DISABLED"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _eval(client, **kw):
    base = {"account_id": "T-100", "channel": "Transf. instantânea"}
    base.update(kw)
    r = client.post("/api/transactions/evaluate", json=base)
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_clean_transaction_approves(client):
    res = _eval(client, account_id="T-clean", beneficiary="T-200",
                amount=50000, sca_passed=True)
    assert res["decision"] == "APPROVE"
    assert res["score"] == 0


def test_new_beneficiary_high_amount_fires(client):
    res = _eval(client, account_id="T-new", beneficiary="T-XYZ",
                amount=4_000_000, sca_passed=False)
    fired = {f["id"] for f in res["fired"]}
    assert "R-002" in fired   # beneficiário novo + montante
    assert "R-014" in fired   # sem SCA
    assert res["score"] >= 50


def test_beneficiary_learned_lowers_score(client):
    acc = "T-learn"
    first = _eval(client, account_id=acc, beneficiary="T-REPEAT",
                  amount=1_500_000, sca_passed=True)
    second = _eval(client, account_id=acc, beneficiary="T-REPEAT",
                   amount=1_500_000, sca_passed=True)
    assert second["score"] < first["score"]  # beneficiário já conhecido


def test_velocity_fires(client):
    acc = "T-vel"
    for _ in range(4):
        last = _eval(client, account_id=acc, beneficiary="T-V1", amount=10000)
    fired = {f["id"] for f in last["fired"]}
    assert "R-001" in fired


def test_impossible_travel(client):
    acc = "T-trav"
    _eval(client, account_id=acc, beneficiary="T-A", amount=10000,
          geo="Luanda", lat=-8.84, lng=13.23)
    res = _eval(client, account_id=acc, beneficiary="T-B", amount=10000,
                geo="Lisboa", lat=38.72, lng=-9.14)
    fired = {f["id"] for f in res["fired"]}
    assert "R-004" in fired


def test_mule_pattern(client):
    acc = "T-mule"
    _eval(client, account_id=acc, direction="in", beneficiary=None, amount=2_000_000)
    res = _eval(client, account_id=acc, direction="out", beneficiary="T-OUT",
                amount=1_900_000)
    fired = {f["id"] for f in res["fired"]}
    assert "R-009" in fired


def test_structuring(client):
    acc = "T-struct"
    for _ in range(3):
        last = _eval(client, account_id=acc, beneficiary="T-S", amount=460000)
    fired = {f["id"] for f in last["fired"]}
    assert "R-008" in fired


def test_rule_toggle_changes_coverage(client):
    before = client.get("/api/killchain").json()["overall"]
    client.patch("/api/rules/R-002/toggle")
    after = client.get("/api/killchain").json()["overall"]
    client.patch("/api/rules/R-002/toggle")  # repõe
    assert after != before


def test_dashboard_keys(client):
    d = client.get("/api/dashboard").json()
    for k in ("cases_active", "alerts_24h", "prevented_amount", "coverage"):
        assert k in d
