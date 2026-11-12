"""Live API tests against the running Postgres + mock data source.

Run with DATA_SOURCE=mock. Uses FastAPI TestClient (drives lifespan → init_db).
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATA_SOURCE", "mock")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # Context manager keeps a single anyio portal/event loop alive for the whole
    # session, so the async SQLAlchemy pool isn't reused across closed loops.
    with TestClient(app) as c:
        yield c


def _unique_email():
    return f"test_{uuid.uuid4().hex[:10]}@tradingsentinel.ai"


@pytest.fixture(scope="module")
def auth(client):
    email = _unique_email()
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123", "name": "Tester"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_duplicate_rejected(client):
    email = _unique_email()
    r1 = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    assert r1.status_code == 201
    r2 = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    assert r2.status_code == 409


def test_login_wrong_password(client):
    email = _unique_email()
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass999"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_token(client, auth):
    r = client.get("/api/v1/auth/me", headers={"Authorization": auth["Authorization"]})
    assert r.status_code == 200
    assert r.json()["email"] == auth["email"]
    assert r.json()["subscription_tier"] == "free"


def test_add_watchlist_and_sentiment(client, auth):
    h = {"Authorization": auth["Authorization"]}
    r = client.post("/api/v1/watchlists", headers=h, json={"symbol": "AAPL", "name": "Apple", "type": "stock"})
    assert r.status_code == 201, r.text
    assert r.json()["symbol"] == "AAPL"

    # Refresh computes & stores sentiment
    wid = r.json()["id"]
    r2 = client.post(f"/api/v1/watchlists/{wid}/refresh", headers=h)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["sentiment"] in ("bull", "bear", "neutral")
    assert 0 <= body["bull_score"] <= 100
    assert 0 <= body["bear_score"] <= 100
    assert abs(body["bull_score"] + body["bear_score"] - 100) < 0.5


def test_watchlist_duplicate_rejected(client, auth):
    h = {"Authorization": auth["Authorization"]}
    client.post("/api/v1/watchlists", headers=h, json={"symbol": "MSFT", "type": "stock"})
    r = client.post("/api/v1/watchlists", headers=h, json={"symbol": "MSFT", "type": "stock"})
    assert r.status_code == 409


def test_free_tier_limit(client):
    # Fresh user, fill the 5-item free limit, 6th must 402
    email = _unique_email()
    token = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    for sym in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]:
        r = client.post("/api/v1/watchlists", headers=h, json={"symbol": sym, "type": "stock"})
        assert r.status_code == 201, f"{sym}: {r.text}"
    r6 = client.post("/api/v1/watchlists", headers=h, json={"symbol": "AMZN", "type": "stock"})
    assert r6.status_code == 402


def test_alert_scan_fires_price_target(client):
    email = _unique_email()
    token = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    add = client.post("/api/v1/watchlists", headers=h, json={"symbol": "AAPL", "type": "stock"}).json()
    wid = add["id"]
    # First scan sets baseline sentiment
    client.post("/api/v1/alerts/scan", headers=h)
    # Set an always-hit target
    client.patch(f"/api/v1/watchlists/{wid}", headers=h, json={"target_price": 1.0})
    r = client.post("/api/v1/alerts/scan", headers=h)
    assert r.status_code == 200
    types = {a["type"] for a in r.json()["alerts"]}
    assert "price_target" in types

    hist = client.get("/api/v1/alerts", headers=h)
    assert hist.status_code == 200
    assert hist.json()["count"] >= 1


def test_telegram_not_linked_errors(client, auth):
    r = client.post("/api/v1/alerts/test-telegram", headers={"Authorization": auth["Authorization"]})
    assert r.status_code == 400  # no telegram linked
