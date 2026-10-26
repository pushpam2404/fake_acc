import io
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import cases
from backend.main import app

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# The lifespan hook is not used here (plain TestClient without `with`), so the
# on-disk backend/cases.db is never touched; cases use an in-memory database.
client = TestClient(app)

BOT_X = {"platform": "twitter", "followers": 3, "following": 4800, "post_count": 9000,
         "verified": 0, "description_length": 0, "account_age_days": 5, "has_url": 0,
         "username": "user918273645", "username_length": 13, "digits_in_username": 9,
         "digit_ratio_username": 0.69}
HUMAN_X = {"platform": "twitter", "followers": 850, "following": 320, "post_count": 4200,
           "verified": 1, "description_length": 140, "account_age_days": 1400, "has_url": 1,
           "username": "devperson", "username_length": 9, "digits_in_username": 0,
           "digit_ratio_username": 0.0}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_analyze_twitter_returns_score_label_and_reasons():
    r = client.post("/analyze", json=BOT_X)
    assert r.status_code == 200
    body = r.json()
    assert body["platform"] == "twitter"
    assert 0 <= body["risk_score"] <= 100
    assert body["classification"] in {"REAL", "SUSPICIOUS", "FAKE"}
    assert body["reasons"]


def test_obvious_bot_scores_higher_than_obvious_human():
    bot = client.post("/analyze", json=BOT_X).json()["risk_score"]
    human = client.post("/analyze", json=HUMAN_X).json()["risk_score"]
    assert bot > human


def test_analyze_meta():
    r = client.post("/analyze", json={"platform": "meta", "followers": 2, "following": 2700,
                                      "post_count": 0, "has_profile_pic": 0, "bio_length": 0})
    assert r.status_code == 200
    assert r.json()["platform"] == "meta"
    assert r.json()["classification"] == "FAKE"


def test_analyze_rejects_missing_required_fields():
    assert client.post("/analyze", json={"followers": 1}).status_code == 422


def test_batch_csv_scores_every_row():
    path = os.path.join(ROOT, "demo_batch.csv")
    with open(path, "rb") as f:
        rows = len(f.read().decode().strip().splitlines()) - 1
    with open(path, "rb") as f:
        r = client.post("/analyze/batch/csv", files={"file": ("demo_batch.csv", f, "text/csv")})
    assert r.status_code == 200
    assert len(r.json()["results"]) == rows


def test_batch_csv_rejects_other_extensions():
    r = client.post("/analyze/batch/csv", files={"file": ("x.txt", io.BytesIO(b"a,b\n1,2"), "text/plain")})
    assert r.status_code == 400


@pytest.fixture()
def case_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    cases.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[cases.get_db] = override
    yield client
    app.dependency_overrides.clear()


def _new_case(c):
    r = c.post("/cases", json={"platform": "twitter", "handle": "bot1", "risk_score": 91.0,
                               "classification": "FAKE", "reasons": ["test"]})
    assert r.status_code == 200, r.text
    return r.json()


def test_case_status_moves_forward_one_step_at_a_time(case_client):
    case = _new_case(case_client)
    assert case["status"] == "FLAGGED"
    skip = case_client.patch(f"/cases/{case['id']}/status", json={"status": "REPORT_SENT"})
    assert skip.status_code == 400
    for nxt in ("UNDER_REVIEW", "REPORT_SENT", "TAKEDOWN_CONFIRMED"):
        r = case_client.patch(f"/cases/{case['id']}/status", json={"status": nxt})
        assert r.status_code == 200 and r.json()["status"] == nxt


def test_closed_case_cannot_be_reopened(case_client):
    case = _new_case(case_client)
    for nxt in ("UNDER_REVIEW", "REPORT_SENT", "TAKEDOWN_CONFIRMED"):
        case_client.patch(f"/cases/{case['id']}/status", json={"status": nxt})
    back = case_client.patch(f"/cases/{case['id']}/status", json={"status": "FLAGGED"})
    assert back.status_code == 400
