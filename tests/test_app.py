import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
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


def test_health_and_metadata(client):
    assert client.get("/api/health").get_json()["status"] == "healthy"
    metadata = client.get("/api/meta").get_json()
    assert "en" in metadata["supported_languages"]
    assert "intent classification" in metadata["features"]


def test_english_chat_is_persisted_and_classified(client):
    response = client.post("/api/chat", json={"message": "How can I improve my CV?", "user_id": "test-user", "language": "en"})
    data = response.get_json()
    assert response.status_code == 200
    assert data["intent"] == "career"
    assert data["confidence"] > 0
    history = client.get("/api/conversations/test-user").get_json()["conversations"]
    assert len(history) == 1
    assert history[0]["message"] == "How can I improve my CV?"


def test_auto_language_detection_and_arabic_response(client):
    response = client.post("/api/chat", json={"message": "ما هو الذكاء الاصطناعي؟", "user_id": "arabic-user", "language": "auto"})
    data = response.get_json()
    assert response.status_code == 200
    assert data["language"] == "ar"
    assert data["intent"] == "ai_basics"
    assert "الذكاء الاصطناعي" in data["response"]


def test_validation_and_feedback_analytics(client):
    assert client.post("/api/chat", json={"message": "", "user_id": "x"}).status_code == 400
    chat = client.post("/api/chat", json={"message": "What is AI?", "user_id": "feedback-user", "language": "en"}).get_json()
    feedback = client.post("/api/feedback", json={"conversation_id": chat["conversation_id"], "user_id": "feedback-user", "rating": 1})
    assert feedback.status_code == 200
    analytics = client.get("/api/analytics/feedback-user").get_json()
    assert analytics["total_messages"] == 1
    assert analytics["satisfaction_rate"] == 1.0
