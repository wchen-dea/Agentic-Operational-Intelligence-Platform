from fastapi.testclient import TestClient

from ai_system.gateway.api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_kpi_store():
    response = client.post("/kpi", json={"store_id": "245"})
    assert response.status_code == 200
    data = response.json()
    assert data["store_id"] == "245"
    assert "revenue_total" in data


def test_kpi_region():
    response = client.post("/kpi", json={"region": "Phoenix"})
    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "Phoenix"
    assert "appointment_show_rate" in data


def test_alerts_store():
    response = client.get("/alerts/245")
    assert response.status_code == 200
    data = response.json()
    assert data["store_id"] == "245"
    assert isinstance(data["alerts"], list)
    assert len(data["alerts"]) > 0


def test_ask_endpoint():
    response = client.post(
        "/ask",
        json={
            "question": "Why are sales low?",
            "store_id": "245",
            "persona": "store_manager",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "kpis" in data
    assert "alerts" in data


def test_operations_brief():
    response = client.post(
        "/operations/brief",
        json={
            "store_id": "245",
            "persona": "executive",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "operational_brief" in data
    assert data["persona"] == "executive"
