"""Test suite for Health and Session API endpoints."""

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


def test_session_lifecycle(client: TestClient):
    """Test full CRUD lifecycle for student study sessions."""
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
    assert created["student_id"] == "student_test_101"

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
    assert session_data["messages"][0]["sender_role"] == "user"

    # 4. List sessions for the student
    list_res = client.get("/api/v1/sessions?student_id=student_test_101")
    assert list_res.status_code == 200
    all_sessions = list_res.json()
    assert any(s["id"] == session_id for s in all_sessions)

    # 5. Delete the session
    del_res = client.delete(f"/api/v1/sessions/{session_id}")
    assert del_res.status_code == 204

    # 6. Verify 404 after deletion
    not_found_res = client.get(f"/api/v1/sessions/{session_id}")
    assert not_found_res.status_code == 404
