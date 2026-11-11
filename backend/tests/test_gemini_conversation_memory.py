"""Live integration & failure-handling tests for Gemini tutoring, system prompt quality, and multi-turn session memory."""

from types import SimpleNamespace
import pytest

from app.core.config import settings
from app.services.tutor_engine import tutor_engine


def _register_and_login(client, email: str, password: str = "StrongPass123!"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Tutor Tester", "grade_level": "Undergraduate"},
    )
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGeminiErrorHandlingNoSilentFallback:
    """Verify explicit HTTP error surfacing and zero silent dictionary/Wikipedia fallback on Gemini failures."""

    def test_missing_api_key_returns_clear_error_without_fallback(self, client, monkeypatch):
        headers = _register_and_login(client, "missing_key@example.com")
        sess_id = client.post(
            "/api/v1/sessions",
            json={"title": "Key Check", "subject": "Mathematics"},
            headers=headers,
        ).json()["id"]

        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        tutor_engine._gemini_client = None
        tutor_engine._configured_api_key = None

        pipe_res = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "types of logic gate",
                "session_id": sess_id,
                "synthesize_voice": False,
            },
            headers=headers,
        )
        assert pipe_res.status_code == 503
        detail = pipe_res.json()["detail"].lower()
        assert "gemini" in detail and "api key" in detail

        # Failed turn must NOT persist fake/orphan messages into session history
        sess_data = client.get(f"/api/v1/sessions/{sess_id}", headers=headers).json()
        assert len(sess_data["messages"]) == 0

    def test_upstream_gemini_failure_does_not_fallback_to_wikipedia_or_dictionary(self, client, monkeypatch):
        headers = _register_and_login(client, "api_fail@example.com")

        class BrokenModels:
            def generate_content(self, *args, **kwargs):
                err = Exception("403 PERMISSION_DENIED: API_KEY_INVALID")
                err.code = 403
                raise err

        broken_client = SimpleNamespace(models=BrokenModels())
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "invalid-test-key")
        monkeypatch.setattr(tutor_engine, "_get_gemini_client", lambda: broken_client)

        res = client.post(
            "/api/v1/tutor/chat",
            json={"session_id": "broken-key-session", "message": "What is conditional probability?"},
            headers=headers,
        )
        assert res.status_code == 502
        detail = res.json()["detail"].lower()
        assert "gemini" in detail
        assert "authentication" in detail or "invalid" in detail

    def test_quota_exhausted_returns_429_without_silent_fallback(self, client, monkeypatch):
        class QuotaModels:
            def generate_content(self, *args, **kwargs):
                err = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
                err.code = 429
                raise err

        quota_client = SimpleNamespace(models=QuotaModels())
        monkeypatch.setattr(tutor_engine, "_get_gemini_client", lambda: quota_client)

        res = client.post(
            "/api/v1/tutor/solve",
            json={"query": "Explain Newton's third law"},
        )
        assert res.status_code == 429
        assert "quota" in res.json()["detail"].lower() or "rate limit" in res.json()["detail"].lower()


class TestSessionAndUserIsolation:
    """Verify conversation history never leaks across users or unrelated sessions."""

    def test_cross_user_session_access_forbidden_in_pipeline_and_chat(self, client):
        headers_a = _register_and_login(client, "owner_a@example.com")
        headers_b = _register_and_login(client, "intruder_b@example.com")

        sess_a_id = client.post(
            "/api/v1/sessions",
            json={"title": "User A Private Session", "subject": "Mathematics"},
            headers=headers_a,
        ).json()["id"]

        res_pipe = client.post(
            "/api/v1/pipeline/execute",
            json={"query": "Give an example.", "session_id": sess_a_id, "synthesize_voice": False},
            headers=headers_b,
        )
        assert res_pipe.status_code == 403

        res_chat = client.post(
            "/api/v1/tutor/chat",
            json={"session_id": sess_a_id, "message": "Give an example."},
            headers=headers_b,
        )
        assert res_chat.status_code == 403

    def test_euclid_theorem_example_followup_and_unrelated_session_isolation(self, client):
        headers = _register_and_login(client, "euclid_student@example.com")

        sess_euclid = client.post(
            "/api/v1/sessions",
            json={"title": "Euclid Study", "subject": "Mathematics"},
            headers=headers,
        ).json()["id"]
        sess_photosynthesis = client.post(
            "/api/v1/sessions",
            json={"title": "Bio Study", "subject": "Biology"},
            headers=headers,
        ).json()["id"]

        # Turn 1 in Session A: Euclid
        r1 = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "Explain Euclid's division lemma.",
                "session_id": sess_euclid,
                "synthesize_voice": False,
            },
            headers=headers,
        )
        assert r1.status_code == 200
        assert r1.json()["citations"] == []  # No unrequested citation clutter

        # Turn 2 in Session A: Vague follow-up -> must stay on Euclid, NOT dictionary meaning of "example"
        r2 = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "Give an example.",
                "session_id": sess_euclid,
                "synthesize_voice": False,
            },
            headers=headers,
        )
        assert r2.status_code == 200
        ans2 = r2.json()["formatted_markdown"].lower()
        assert "audit notice" not in ans2
        assert any(k in ans2 for k in ("euclid", "remainder", "quotient", "divisor", "gcd", "divide"))

        # Turn 1 in Session B: Independent topic must NOT bleed from Session A
        r_b1 = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "What is osmosis?",
                "session_id": sess_photosynthesis,
                "synthesize_voice": False,
            },
            headers=headers,
        )
        assert r_b1.status_code == 200
        r_b2 = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "Give an example.",
                "session_id": sess_photosynthesis,
                "synthesize_voice": False,
            },
            headers=headers,
        )
        assert r_b2.status_code == 200
        ans_b2 = r_b2.json()["formatted_markdown"].lower()
        assert "euclid" not in ans_b2
        assert any(k in ans_b2 for k in ("water", "membrane", "cell", "plant", "root", "osmosis"))


class TestSixTurnLogicGatesConversation:
    """Tests the exact 6-turn sequential tutoring conversation end-to-end with real Gemini responses."""

    def test_logic_gates_six_turn_conversation_workflow(self, client):
        headers = _register_and_login(client, "logic_gates_student@example.com")
        sess_id = client.post(
            "/api/v1/sessions",
            json={"title": "Digital Logic Gates", "subject": "Computer Science"},
            headers=headers,
        ).json()["id"]

        def ask(q: str):
            res = client.post(
                "/api/v1/pipeline/execute",
                json={
                    "query": q,
                    "session_id": sess_id,
                    "level": "intermediate",
                    "synthesize_voice": False,
                },
                headers=headers,
            )
            assert res.status_code == 200, f"Failed on '{q}': {res.text}"
            payload = res.json()
            md = payload["formatted_markdown"]
            assert payload["citations"] == [], f"Unexpected unrequested citations on '{q}': {payload['citations']}"
            assert "Answer Verification & Audit Notice" not in md, f"Unexpected audit banner on '{q}':\n{md}"
            assert "Unverified Citation" not in md, f"Unexpected citation rewrite on '{q}':\n{md}"
            return md

        # 1. Explain types of logic gates.
        t1 = ask("Explain types of logic gates.")
        t1_low = t1.lower()
        assert all(g in t1_low for g in ("and", "or", "not"))
        assert len(t1) > 250

        # 2. Give their truth tables.
        t2 = ask("Give their truth tables.")
        t2_low = t2.lower()
        assert "|" in t2  # Markdown truth tables
        assert all(g in t2_low for g in ("and", "or", "not"))

        # 3. Explain AND gate with an example.
        t3 = ask("Explain AND gate with an example.")
        t3_low = t3.lower()
        assert "and" in t3_low
        assert "example" in t3_low or "suppose" in t3_low or "switch" in t3_low

        # 4. Write a C program for AND gate.
        t4 = ask("Write a C program for AND gate.")
        t4_low = t4.lower()
        assert "```c" in t4_low
        assert "#include" in t4 and "printf" in t4

        # 5. Explain the code line by line.
        t5 = ask("Explain the code line by line.")
        t5_low = t5.lower()
        assert any(tok in t5_low for tok in ("#include", "stdio.h", "main", "printf"))

        # 6. Give me a practice question.
        t6 = ask("Give me a practice question.")
        t6_low = t6.lower()
        assert any(k in t6_low for k in ("logic gate", "and gate", "input", "output", "truth table", "boolean"))

        # Verify all 12 messages persisted chronologically in DB
        sess_data = client.get(f"/api/v1/sessions/{sess_id}", headers=headers).json()
        msgs = sess_data["messages"]
        assert len(msgs) == 12
        roles = [m["sender_role"] for m in msgs]
        assert roles == ["user", "assistant"] * 6

