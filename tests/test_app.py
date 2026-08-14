import os

os.environ["SECRET_KEY"] = "test-secret"

import pytest

import app as app_module
from app import app, db
from src.database.models import PasswordResetToken


@pytest.fixture()
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register(client, email, password="strong-pass-123", display_name="Test User"):
    return client.post("/api/auth/register", json={"email": email, "password": password, "display_name": display_name})


def login(client, email, password="strong-pass-123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_public_health_and_protected_api(client):
    assert client.get("/api/health").get_json()["status"] == "healthy"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/conversations").status_code == 401
    assert client.get("/api/analytics").status_code == 401
    assert client.post("/api/chat", json={"message": "What is AI?"}).status_code == 401


def test_register_login_me_and_password_hash(client):
    response = register(client, "student@example.com")
    assert response.status_code == 201
    user = response.get_json()["user"]
    assert user["email"] == "student@example.com"
    assert "password_hash" not in user
    assert client.get("/api/auth/me").get_json()["authenticated"] is True

    client.post("/api/auth/logout")
    assert login(client, "student@example.com", "wrong-password").status_code == 401
    assert login(client, "student@example.com").status_code == 200
    assert register(client, "student@example.com").status_code == 409


def test_registration_validation(client):
    assert register(client, "not-an-email", "strong-pass-123").status_code == 400
    assert register(client, "short@example.com", "short").status_code == 400


def test_chat_history_and_analytics_belong_to_authenticated_user(client):
    register(client, "owner@example.com", display_name="Owner")
    chat = client.post("/api/chat", json={"message": "How can I improve my CV?", "language": "en"})
    data = chat.get_json()
    assert chat.status_code == 200
    assert data["intent"] == "career"
    conversation_id = data["conversation_id"]
    assert len(client.get("/api/conversations").get_json()["conversations"]) == 1

    client.post("/api/auth/logout")
    register(client, "other@example.com", display_name="Other")
    assert client.get("/api/conversations").get_json()["conversations"] == []
    assert client.post("/api/feedback", json={"conversation_id": conversation_id, "rating": 1}).status_code == 404
    assert client.get("/api/analytics").get_json()["total_messages"] == 0


def test_feedback_and_arabic_chat(client):
    register(client, "arabic@example.com")
    chat = client.post("/api/chat", json={"message": "ما هو الذكاء الاصطناعي؟", "language": "auto"})
    data = chat.get_json()
    assert data["language"] == "ar"
    assert data["intent"] == "ai_basics"
    feedback = client.post("/api/feedback", json={"conversation_id": data["conversation_id"], "rating": 1})
    assert feedback.status_code == 200
    analytics = client.get("/api/analytics").get_json()
    assert analytics["total_messages"] == 1
    assert analytics["satisfaction_rate"] == 1.0


def test_password_reset_is_single_use_and_updates_password(client, monkeypatch):
    register(client, "reset@example.com")
    captured = {}

    def fake_send(user, raw_token):
        captured["token"] = raw_token
        return False

    monkeypatch.setattr(app_module, "send_reset_email", fake_send)
    request = client.post("/api/auth/request-reset", json={"email": "reset@example.com"})
    assert request.status_code == 202
    assert "token" in captured
    with app.app_context():
        stored = PasswordResetToken.query.one()
        assert stored.token_hash != captured["token"]

    reset = client.post("/api/auth/reset-password", json={"token": captured["token"], "password": "new-strong-pass-123", "confirm_password": "new-strong-pass-123"})
    assert reset.status_code == 200
    client.post("/api/auth/logout")
    assert login(client, "reset@example.com", "strong-pass-123").status_code == 401
    assert login(client, "reset@example.com", "new-strong-pass-123").status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": captured["token"], "password": "another-pass-123", "confirm_password": "another-pass-123"}).status_code == 400


def test_reset_request_does_not_enumerate_accounts(client):
    existing = client.post("/api/auth/request-reset", json={"email": "existing@example.com"})
    missing = client.post("/api/auth/request-reset", json={"email": "missing@example.com"})
    assert existing.status_code == missing.status_code == 202
    assert existing.get_json() == missing.get_json()


def test_advanced_dashboard_returns_user_scoped_time_series(client):
    register(client, "dashboard@example.com")
    client.post("/api/chat", json={"message": "How do I prepare for an interview?", "language": "en"})
    dashboard = client.get("/api/analytics/dashboard?days=7")
    data = dashboard.get_json()
    assert dashboard.status_code == 200
    assert data["period_days"] == 7
    assert data["total_messages"] == 1
    assert data["active_days"] == 1
    assert data["top_intent"] == "career"
    assert data["intent_breakdown"]["career"] == 1
    assert len(data["daily_activity"]) == 1


def test_google_oauth_requires_configuration(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    response = client.get("/api/auth/google")
    assert response.status_code == 503
    assert "not configured" in response.get_json()["error"]
