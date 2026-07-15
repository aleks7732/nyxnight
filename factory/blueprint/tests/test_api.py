from datetime import date

from fastapi.testclient import TestClient

from nyxnight.api import app

client = TestClient(app)


def payload() -> dict[str, object]:
    return {
        "city": "Chicago",
        "date": "2027-10-17",
        "party_size": 4,
        "budget_per_person": 140,
        "vibe": "cozy live jazz",
        "start_time": "18:00",
        "end_time": "23:30",
    }


def test_health_and_static_ui() -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "service": "nyxnight",
        "mode": "demo",
    }
    root = client.get("/")
    assert root.status_code == 200
    assert "NyxNight" in root.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_plan_contract() -> None:
    response = client.post("/api/plan", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Chicago"
    assert body["date"] == date(2027, 10, 17).isoformat()
    assert body["mode"] == "demo"
    assert len(body["stops"]) == 3
    assert body["estimated_total_per_person"] <= 140


def test_invalid_window_is_bounded_validation_error() -> None:
    invalid = payload()
    invalid["end_time"] = "19:00"
    response = client.post("/api/plan", json=invalid)
    assert response.status_code == 422
    assert "time window" in response.text
