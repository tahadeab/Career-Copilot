import os

os.environ["SECRET_KEY"] = "test-secret"

import pytest

from app import app, db


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
