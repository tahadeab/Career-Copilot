"""Career Copilot: an explainable bilingual AI chatbot for students and early-career builders."""

import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import func

from src.database.models import Conversation, Feedback, User, db
from src.services.chatbot_service import ChatbotService
from src.services.language_service import LanguageService

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("career_copilot")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "career-copilot-development-key"),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///career_copilot.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JSON_SORT_KEYS=False,
)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*").split(",")}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
db.init_app(app)

chatbot_service = ChatbotService()
language_service = LanguageService()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def ensure_user(user_id: str, language: str) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        user = User(id=user_id, language_preference=language)
        db.session.add(user)
    else:
        user.language_preference = language
    return user


with app.app_context():
    db.create_all()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "career-copilot", "version": "2.0.0", "timestamp": utc_now()})


@app.get("/api/meta")
def metadata():
    return jsonify({
        "name": "Career Copilot",
        "description": "An explainable bilingual AI assistant for learning, graduation projects, and career preparation.",
        "supported_languages": list(language_service.supported_languages),
        "features": ["intent classification", "sentiment signals", "persistent history", "feedback loop", "REST API", "real-time events"],
    })


@app.get("/api/suggestions")
def suggestions():
    language = request.args.get("language", "en")
    return jsonify({"language": language, "suggestions": chatbot_service.get_suggested_questions(language)})


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    user_id = str(data.get("user_id", "anonymous")).strip()[:100] or "anonymous"
    language = str(data.get("language", "auto")).lower()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message must be 2,000 characters or fewer"}), 400
    if language == "auto":
        language = language_service.detect_language(message)
    if language not in language_service.supported_languages:
        return jsonify({"error": "Unsupported language. Use en, ar, or auto."}), 400

    try:
        result = chatbot_service.process_message(message, user_id, language)
        user = ensure_user(user_id, language)
        conversation = Conversation(
            user=user,
            message=message,
            response=result.response,
            language=language,
            intent=result.intent,
            confidence=result.confidence,
            sentiment=result.sentiment,
        )
        db.session.add(conversation)
        db.session.commit()
        return jsonify({
            "response": result.response,
            "language": language,
            "conversation_id": conversation.id,
            "intent": result.intent,
            "confidence": result.confidence,
            "sentiment": result.sentiment,
            "timestamp": conversation.timestamp.isoformat(),
        })
    except Exception:
        db.session.rollback()
        logger.exception("Chat request failed")
        return jsonify({"error": "Unable to process the message right now"}), 500


@app.get("/api/conversations/<user_id>")
def get_conversations(user_id):
    limit = min(max(request.args.get("limit", 50, type=int), 1), 100)
    conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.timestamp.desc()).limit(limit).all()
    return jsonify({"conversations": [conversation.to_dict() for conversation in conversations]})


@app.post("/api/feedback")
def submit_feedback():
    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id")
    user_id = str(data.get("user_id", "")).strip()[:100]
    rating = data.get("rating")
    comment = str(data.get("comment", "")).strip()[:500] or None
    if not conversation_id or not user_id or rating not in (0, 1):
        return jsonify({"error": "conversation_id, user_id, and rating (0 or 1) are required"}), 400
    conversation = db.session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        return jsonify({"error": "Conversation not found"}), 404
    feedback = Feedback.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()
    if feedback is None:
        feedback = Feedback(conversation_id=conversation_id, user_id=user_id, rating=rating, comment=comment)
        db.session.add(feedback)
    else:
        feedback.rating, feedback.comment = rating, comment
    db.session.commit()
    return jsonify({"message": "Feedback saved", "feedback": feedback.to_dict()})


@app.get("/api/analytics/<user_id>")
def analytics(user_id):
    total = Conversation.query.filter_by(user_id=user_id).count()
    positive = Feedback.query.filter_by(user_id=user_id, rating=1).count()
    negative = Feedback.query.filter_by(user_id=user_id, rating=0).count()
    intents = db.session.query(Conversation.intent, func.count(Conversation.id)).filter_by(user_id=user_id).group_by(Conversation.intent).all()
    return jsonify({
        "user_id": user_id,
        "total_messages": total,
        "feedback": {"positive": positive, "negative": negative, "total": positive + negative},
        "satisfaction_rate": round(positive / (positive + negative), 3) if positive + negative else None,
        "intent_breakdown": {intent: count for intent, count in intents},
    })


@app.post("/api/translate")
def translate_text():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    target = str(data.get("target_language", "en")).lower()
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400
    try:
        return jsonify({"original_text": text, "translated_text": language_service.translate_text(text, target), "target_language": target})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@socketio.on("connect")
def handle_connect():
    emit("connected", {"message": "Connected to Career Copilot", "version": "2.0.0"})


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Realtime client disconnected")


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        allow_unsafe_werkzeug=True,
    )
