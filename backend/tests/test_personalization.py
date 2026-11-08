"""Test suite for Phase 9: Conversation History, Student Personalization, and Privacy Controls."""

import pytest
from app.services.context_manager import context_manager
from app.models.session import StudySession, SessionMessage


def get_auth_token(client, email="student_phase9@example.com", password="SecurePassword123!"):
    """Helper to register and login a user, returning a Bearer Authorization header."""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Student",
            "grade_level": "Grade 11 STEM",
        },
    )
    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSessionCRUDAndRenaming:
    """Tests session creation, inline renaming, listing, and deletion."""

    def test_session_lifecycle(self, client):
        headers = get_auth_token(client, email="alice@example.com")

        # 1. Create Session
        res = client.post(
            "/api/v1/sessions",
            json={"title": "Quadratic Formula Exploration", "subject": "Mathematics"},
            headers=headers,
        )
        assert res.status_code == 201
        session_data = res.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Quadratic Formula Exploration"
        assert session_data["subject"] == "Mathematics"

        # 2. Rename Session (PUT /sessions/{id})
        rename_res = client.put(
            f"/api/v1/sessions/{session_id}",
            json={"title": "Advanced Polynomial Roots"},
            headers=headers,
        )
        assert rename_res.status_code == 200
        assert rename_res.json()["title"] == "Advanced Polynomial Roots"

        # 3. Retrieve Session by ID
        get_res = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Advanced Polynomial Roots"

        # 4. List Sessions
        list_res = client.get("/api/v1/sessions", headers=headers)
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(s["id"] == session_id for s in items)

        # 5. Delete Session
        del_res = client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
        assert del_res.status_code == 204

        # 6. Verify Session is gone
        get_again = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert get_again.status_code == 404


class TestMessageStorageAndMetadata:
    """Tests persistence of multimodal input type, extracted question, citations, and audio references."""

    def test_message_storage_with_multimodal_attributes(self, client):
        headers = get_auth_token(client, email="bob@example.com")

        # Create session
        res = client.post(
            "/api/v1/sessions",
            json={"title": "Physics Optics", "subject": "Physics"},
            headers=headers,
        )
        session_id = res.json()["id"]

        # Post user question originating from an image upload
        user_msg_res = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={
                "sender_role": "user",
                "content_type": "image",
                "input_type": "image",
                "extracted_question": "Calculate the focal length using the lens formula 1/f = 1/v - 1/u",
                "content": "[Uploaded Optical Diagram]",
            },
            headers=headers,
        )
        assert user_msg_res.status_code == 201
        user_msg = user_msg_res.json()
        assert user_msg["input_type"] == "image"
        assert "lens formula" in user_msg["extracted_question"]

        # Post assistant tutor response with citations and audio URL
        assistant_msg_res = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={
                "sender_role": "assistant",
                "content_type": "text",
                "input_type": "text",
                "content": "To calculate the focal length, let's identify the sign conventions.",
                "audio_url": "/api/v1/voice/audio/test_lens_output.mp3",
                "citations_json": [
                    {
                        "source_name": "NCERT Class 10 Physics",
                        "chapter": "Light: Reflection and Refraction",
                        "page_number": 182,
                    }
                ],
            },
            headers=headers,
        )
        assert assistant_msg_res.status_code == 201
        assistant_msg = assistant_msg_res.json()
        assert assistant_msg["audio_url"] == "/api/v1/voice/audio/test_lens_output.mp3"
        assert len(assistant_msg["citations"]) == 1
        assert assistant_msg["citations"][0]["source_name"] == "NCERT Class 10 Physics"

        # Verify full session fetch returns both messages with enriched fields
        session_full = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
        assert len(session_full["messages"]) == 2
        assert session_full["messages"][0]["input_type"] == "image"
        assert session_full["messages"][1]["audio_url"] == "/api/v1/voice/audio/test_lens_output.mp3"


class TestStudentPreferences:
    """Tests updating and reading student learning and speech preferences."""

    def test_preferences_defaults_and_update(self, client):
        headers = get_auth_token(client, email="charlie@example.com")

        # 1. Fetch initial default preferences
        get_res = client.get("/api/v1/users/preferences", headers=headers)
        assert get_res.status_code == 200
        pref = get_res.json()
        assert pref["preferred_explanation_level"] == "intermediate"
        assert pref["preferred_playback_speed"] == 1.0
        assert pref["preferred_language"] == "en"

        # 2. Update preferences
        update_res = client.put(
            "/api/v1/users/preferences",
            json={
                "preferred_explanation_level": "advanced",
                "preferred_voice": "en-US-ChristopherNeural",
                "preferred_playback_speed": 1.25,
                "preferred_language": "de",
                "preferred_subjects": ["Mathematics", "Computer Science"],
            },
            headers=headers,
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["preferred_explanation_level"] == "advanced"
        assert updated["preferred_voice"] == "en-US-ChristopherNeural"
        assert updated["preferred_playback_speed"] == 1.25
        assert updated["preferred_language"] == "de"
        assert updated["preferred_subjects"] == ["Mathematics", "Computer Science"]

        # 3. Verify persistence
        verify_res = client.get("/api/v1/users/preferences", headers=headers)
        assert verify_res.status_code == 200
        persisted = verify_res.json()
        assert persisted["preferred_explanation_level"] == "advanced"
        assert persisted["preferred_language"] == "de"


class TestPrivacyAndAccessControl:
    """Tests strict tenant isolation: User A cannot read, modify, or delete User B's sessions or files."""

    def test_cross_user_session_isolation(self, client):
        headers_user_a = get_auth_token(client, email="user_a@example.com")
        headers_user_b = get_auth_token(client, email="user_b@example.com")

        # User A creates a session
        create_res = client.post(
            "/api/v1/sessions",
            json={"title": "User A Private Research", "subject": "Chemistry"},
            headers=headers_user_a,
        )
        assert create_res.status_code == 201
        session_a_id = create_res.json()["id"]

        # User B attempts to view User A's session -> 403 Forbidden
        view_res = client.get(f"/api/v1/sessions/{session_a_id}", headers=headers_user_b)
        assert view_res.status_code == 403
        assert "permission" in view_res.json()["detail"].lower()

        # User B attempts to rename User A's session -> 403 Forbidden
        rename_res = client.put(
            f"/api/v1/sessions/{session_a_id}",
            json={"title": "Hacked Title"},
            headers=headers_user_b,
        )
        assert rename_res.status_code == 403

        # User B attempts to append a message to User A's session -> 403 Forbidden
        msg_res = client.post(
            f"/api/v1/sessions/{session_a_id}/messages",
            json={"sender_role": "user", "content": "Unauthorized message"},
            headers=headers_user_b,
        )
        assert msg_res.status_code == 403

        # User B attempts to delete User A's session -> 403 Forbidden
        del_res = client.delete(f"/api/v1/sessions/{session_a_id}", headers=headers_user_b)
        assert del_res.status_code == 403

        # User A session is still intact for User A
        owner_res = client.get(f"/api/v1/sessions/{session_a_id}", headers=headers_user_a)
        assert owner_res.status_code == 200
        assert owner_res.json()["title"] == "User A Private Research"

    def test_cross_user_file_privacy(self, client):
        headers_user_a = get_auth_token(client, email="user_file_a@example.com")
        headers_user_b = get_auth_token(client, email="user_file_b@example.com")

        # User A uploads a text file
        upload_res = client.post(
            "/api/v1/ingest/upload",
            files={"file": ("confidential_notes.txt", b"Secret academic findings", "text/plain")},
            headers=headers_user_a,
        )
        assert upload_res.status_code == 201
        asset_id = upload_res.json()["asset_id"]

        # User A can view their own asset metadata
        user_a_asset_res = client.get(f"/api/v1/ingest/assets/{asset_id}", headers=headers_user_a)
        assert user_a_asset_res.status_code == 200

        # User B attempts to access User A's asset -> 403 Forbidden
        user_b_asset_res = client.get(f"/api/v1/ingest/assets/{asset_id}", headers=headers_user_b)
        assert user_b_asset_res.status_code == 403
        assert "private asset" in user_b_asset_res.json()["detail"].lower()


class TestContextManagementAndAnaphora:
    """Tests follow-up detection, context extraction, and session isolation in ContextManager."""

    def test_anaphoric_follow_up_detection(self):
        assert context_manager.is_follow_up_inquiry("What about when x = 5?") is True
        assert context_manager.is_follow_up_inquiry("Can you explain step 2 in more detail?") is True
        assert context_manager.is_follow_up_inquiry("Why is that the formula?") is True
        assert context_manager.is_follow_up_inquiry("What if the discriminant is negative?") is True
        assert context_manager.is_follow_up_inquiry("Repeat the last part please.") is True

        # Fresh non-follow-up questions
        assert context_manager.is_follow_up_inquiry("What is Photosynthesis?") is False
        assert context_manager.is_follow_up_inquiry("State Newton's third law of motion.") is False

    def test_context_extraction_and_session_isolation(self, db_session):
        # Create Session 1
        s1 = StudySession(student_id="student_ctx", title="Session 1", subject="Math")
        db_session.add(s1)
        db_session.commit()
        db_session.refresh(s1)

        # Add initial conversation to Session 1
        m1 = SessionMessage(
            session_id=s1.id,
            sender_role="user",
            content="How do I find the roots of ax^2 + bx + c = 0?",
            extracted_question="How do I find the roots of ax^2 + bx + c = 0?",
        )
        m2 = SessionMessage(
            session_id=s1.id,
            sender_role="assistant",
            content="Use the quadratic formula: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$.",
        )
        db_session.add_all([m1, m2])
        db_session.commit()

        # Follow-up inside Session 1
        turns, is_follow_up, summary = context_manager.extract_relevant_context(
            session_id=s1.id,
            current_query="What if that root is imaginary?",
            db=db_session,
        )
        assert is_follow_up is True
        assert len(turns) == 2
        assert summary is not None
        assert "Governing equations:" in summary
        assert "b^2 - 4ac" in summary

        # Fresh query in new Session 2 (zero bleed)
        s2 = StudySession(student_id="student_ctx", title="Session 2", subject="History")
        db_session.add(s2)
        db_session.commit()
        db_session.refresh(s2)

        turns_s2, is_follow_up_s2, summary_s2 = context_manager.extract_relevant_context(
            session_id=s2.id,
            current_query="What if that root is imaginary?",
            db=db_session,
        )
        # Session 2 has 0 prior turns, so turns list is empty and summary is None
        assert len(turns_s2) == 0
        assert summary_s2 is None

        # None session_id returns empty context
        turns_none, is_follow_up_none, summary_none = context_manager.extract_relevant_context(
            session_id=None,
            current_query="What if that root is imaginary?",
            db=db_session,
        )
        assert len(turns_none) == 0
        assert summary_none is None

