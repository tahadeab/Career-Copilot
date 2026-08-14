"""Career Copilot: an explainable bilingual AI chatbot with secure user accounts."""

import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import func, inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import Conversation, Feedback, User, db
from src.services.chatbot_service import ChatbotService
from src.services.language_service import LanguageService

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("career_copilot")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "change-this-development-secret"),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///career_copilot.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*").split(",")}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
db.init_app(app)

chatbot_service = ChatbotService()
language_service = LanguageService()
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def migrate_user_columns():
    """Add authentication columns to an existing SQLite database without destroying data."""
    if db.engine.dialect.name != "sqlite":
        return
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    additions = {
        "email": "VARCHAR(255)",
        "display_name": "VARCHAR(120)",
        "password_hash": "VARCHAR(255)",
    }
    with db.engine.begin() as connection:
        for column, sql_type in additions.items():
            if column not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {sql_type}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))


with app.app_context():
    db.create_all()
    migrate_user_columns()


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            session.clear()
            return jsonify({"error": "Authentication required"}), 401
        return view(user, *args, **kwargs)

    return wrapped


def validate_registration(data):
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    display_name = str(data.get("display_name", "")).strip()[:120]
    if not EMAIL_PATTERN.match(email) or len(email) > 255:
        return None, "A valid email address is required"
    if len(password) < 8:
        return None, "Password must contain at least 8 characters"
    if len(password) > 128:
        return None, "Password must contain 128 characters or fewer"
    return {"email": email, "password": password, "display_name": display_name or email.split("@")[0]}, None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "career-copilot", "version": "2.1.0", "timestamp": utc_now()})


@app.get("/api/meta")
def metadata():
    return jsonify({
        "name": "Career Copilot",
        "description": "An explainable bilingual AI assistant for learning, graduation projects, and career preparation.",
        "supported_languages": list(language_service.supported_languages),
        "features": ["secure authentication", "private conversation history", "intent classification", "sentiment signals", "feedback loop", "REST API", "real-time events"],
    })


@app.post("/api/auth/register")
def register():
    payload, error = validate_registration(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    if User.query.filter(func.lower(User.email) == payload["email"]).first():
        return jsonify({"error": "An account with this email already exists"}), 409
    user = User(
        id=str(uuid.uuid4()),
        email=payload["email"],
        display_name=payload["display_name"],
        password_hash=generate_password_hash(payload["password"]),
        language_preference="en",
    )
    db.session.add(user)
    db.session.commit()
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    return jsonify({"message": "Account created", "user": user.to_dict()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = User.query.filter(func.lower(User.email) == email).first()
    if user is None or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    return jsonify({"message": "Signed in", "user": user.to_dict()})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Signed out"})


@app.get("/api/auth/me")
@login_required
def me(user):
    return jsonify({"authenticated": True, "user": user.to_dict()})


@app.get("/api/suggestions")
def suggestions():
    language = request.args.get("language", "en")
    return jsonify({"language": language, "suggestions": chatbot_service.get_suggested_questions(language)})


@app.post("/api/chat")
@login_required
def chat(user):
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
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
        result = chatbot_service.process_message(message, user.id, language)
        user.language_preference = language
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


@app.get("/api/conversations")
@login_required
def get_conversations(user):
    limit = min(max(request.args.get("limit", 50, type=int), 1), 100)
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.timestamp.desc()).limit(limit).all()
    return jsonify({"conversations": [conversation.to_dict() for conversation in conversations]})


@app.post("/api/feedback")
@login_required
def submit_feedback(user):
    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id")
    rating = data.get("rating")
    comment = str(data.get("comment", "")).strip()[:500] or None
    if not conversation_id or rating not in (0, 1):
        return jsonify({"error": "conversation_id and rating (0 or 1) are required"}), 400
    conversation = db.session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        return jsonify({"error": "Conversation not found"}), 404
    feedback = Feedback.query.filter_by(conversation_id=conversation_id, user_id=user.id).first()
    if feedback is None:
        feedback = Feedback(conversation_id=conversation_id, user_id=user.id, rating=rating, comment=comment)
        db.session.add(feedback)
    else:
        feedback.rating, feedback.comment = rating, comment
    db.session.commit()
    return jsonify({"message": "Feedback saved", "feedback": feedback.to_dict()})


@app.get("/api/analytics")
@login_required
def analytics(user):
    total = Conversation.query.filter_by(user_id=user.id).count()
    positive = Feedback.query.filter_by(user_id=user.id, rating=1).count()
    negative = Feedback.query.filter_by(user_id=user.id, rating=0).count()
    intents = db.session.query(Conversation.intent, func.count(Conversation.id)).filter_by(user_id=user.id).group_by(Conversation.intent).all()
    return jsonify({
        "user_id": user.id,
        "total_messages": total,
        "feedback": {"positive": positive, "negative": negative, "total": positive + negative},
        "satisfaction_rate": round(positive / (positive + negative), 3) if positive + negative else None,
        "intent_breakdown": {intent: count for intent, count in intents},
    })


@app.post("/api/translate")
def translate_text():
    data = request.get_json(silent=True) or {}
    text_value = str(data.get("text", "")).strip()
    target = str(data.get("target_language", "en")).lower()
    if not text_value:
        return jsonify({"error": "Text cannot be empty"}), 400
    try:
        return jsonify({"original_text": text_value, "translated_text": language_service.translate_text(text_value, target), "target_language": target})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@socketio.on("connect")
def handle_connect():
    if current_user() is None:
        return False
    emit("connected", {"message": "Connected to Career Copilot", "version": "2.1.0"})


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
