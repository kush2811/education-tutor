"""Comprehensive test suite for Phase 1 Backend Foundation."""

import io
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns valid system metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "version" in data
    assert data["docs_url"] == "/docs"


def test_health_check(client: TestClient):
    """Test /api/v1/health returns healthy and database connected."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "connected"


def test_auth_registration_and_login(client: TestClient):
    """Test user registration, login, and /me profile retrieval."""
    reg_payload = {
        "email": "student1@example.com",
        "password": "SecurePassword123!",
        "full_name": "Aarav Sharma",
        "grade_level": "Grade 11 STEM"
    }
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "student1@example.com"
    assert user_data["full_name"] == "Aarav Sharma"

    # 2. Login
    login_payload = {
        "email": "student1@example.com",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Retrieve /me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "student1@example.com"

    # 4. Test dashboard endpoint
    dash_res = client.get("/api/v1/users/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["user_id"] == user_data["id"]
    assert "total_sessions" in dash_data
    assert "recommended_topics" in dash_data

    # 5. Fail login with wrong password
    bad_login = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "WrongPassword"})
    assert bad_login.status_code == 401


def test_session_lifecycle(client: TestClient):
    """Test full CRUD lifecycle for student study sessions (conversations)."""
    # 1. Create a session
    payload = {
        "student_id": "student_test_101",
        "title": "Calculus Derivatives & Integrals",
        "subject": "Mathematics",
    }
    create_res = client.post("/api/v1/sessions", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    session_id = created["id"]
    assert created["title"] == "Calculus Derivatives & Integrals"

    # 2. Append a user message
    msg_payload = {
        "sender_role": "user",
        "content_type": "text",
        "content": "Can you explain how the chain rule works with trigonometric functions?",
    }
    msg_res = client.post(f"/api/v1/sessions/{session_id}/messages", json=msg_payload)
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["content"] == msg_payload["content"]
    assert msg_data["session_id"] == session_id

    # 3. Retrieve session with message history
    get_res = client.get(f"/api/v1/sessions/{session_id}")
    assert get_res.status_code == 200
    session_data = get_res.json()
    assert len(session_data["messages"]) == 1

    # 4. List sessions
    list_res = client.get("/api/v1/sessions?student_id=student_test_101")
    assert list_res.status_code == 200
    all_sessions = list_res.json()
    assert any(s["id"] == session_id for s in all_sessions)

    # 5. Delete session
    del_res = client.delete(f"/api/v1/sessions/{session_id}")
    assert del_res.status_code == 204


def test_file_upload(client: TestClient):
    """Test file upload validation and storage recording."""
    fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    files = {"file": ("test_diagram.png", io.BytesIO(fake_image_bytes), "image/png")}
    response = client.post("/api/v1/ingest/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["file_type"] == "image"
    assert "asset_id" in data
