import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "3.0.0" in data["version"]

def test_auth_register_and_login():
    # Register
    user_payload = {
        "email": "doctor_test@medical.ai",
        "password": "Password123@",
        "full_name": "Bác Sĩ Nguyễn Văn A",
        "role": "doctor"
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code in [200, 400]
    
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "doctor_test@medical.ai",
        "password": "Password123@"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "doctor"

def test_triage_analyze_endpoint():
    payload = {
        "user_text": "Tôi bị sốt cao 39 độ, đau đầu dữ dội và người mệt lả",
        "lab_indicators": {}
    }
    response = client.post("/api/v1/medical/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "triage_results" in data
    assert len(data["triage_results"]) > 0
    assert "extracted_entities" in data

def test_admin_glossary_crud():
    # Get Glossary
    res = client.get("/api/v1/admin/glossary")
    assert res.status_code == 200
    assert isinstance(res.json(), dict)
