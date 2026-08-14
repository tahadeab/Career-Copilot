"""Career Copilot: an explainable bilingual AI chatbot with secure accounts and analytics."""

import hashlib
import logging
import os
import re
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import func, inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import Conversation, Feedback, PasswordResetToken, User, db
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
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


def utc_datetime():
    return datetime.now(timezone.utc)


def utc_now():
    return utc_datetime().isoformat()


def as_aware(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


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
        "auth_provider": "VARCHAR(30) NOT NULL DEFAULT 'local'",
        "google_sub": "VARCHAR(255)",
        "last_login_at": "DATETIME",
        "login_count": "INTEGER NOT NULL DEFAULT 0",
    }
    with db.engine.begin() as connection:
        for column, sql_type in additions.items():
            if column not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {sql_type}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)"))


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


def validate_password(password, confirmation=None):
    password = str(password or "")
    if len(password) < 8:
        return "Password must contain at least 8 characters"
    if len(password) > 128:
        return "Password must contain 128 characters or fewer"
    if confirmation is not None and password != str(confirmation):
        return "Passwords do not match"
    return None


def validate_registration(data):
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    display_name = str(data.get("display_name", "")).strip()[:120]
    if not EMAIL_PATTERN.match(email) or len(email) > 255:
        return None, "A valid email address is required"
    error = validate_password(password)
    if error:
        return None, error
    return {"email": email, "password": password, "display_name": display_name or email.split("@")[0]}, None


def record_login(user):
    user.last_login_at = utc_datetime()
    user.login_count = (user.login_count or 0) + 1
    db.session.commit()
    session.clear()
    session.permanent = True
    session["user_id"] = user.id


def send_reset_email(user, raw_token):
    base_url = os.getenv("APP_BASE_URL", request.host_url.rstrip("/"))
    reset_url = f"{base_url}/?reset_token={raw_token}"
    message = EmailMessage()
    message["Subject"] = "Reset your Career Copilot password"
    message["From"] = os.getenv("MAIL_FROM", "no-reply@career-copilot.local")
    message["To"] = user.email
    message.set_content(
        "We received a request to reset your Career Copilot password.\n\n"
        f"Use this link within 30 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning("SMTP is not configured; development reset URL: %s", reset_url)
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    return True


def google_configured():
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def google_redirect_uri():
    return os.getenv("GOOGLE_REDIRECT_URI", f"{request.host_url.rstrip('/')}/api/auth/google/callback")


def login_google_user(profile):
    email = str(profile.get("email", "")).strip().lower()
    google_sub = str(profile.get("sub", ""))
    if not email or not google_sub or not profile.get("email_verified", False):
        raise ValueError("Google account email is not verified")
    user = User.query.filter_by(google_sub=google_sub).first() or User.query.filter(func.lower(User.email) == email).first()
    if user is None:
        user = User(id=str(uuid.uuid4()), email=email, display_name=profile.get("name") or email.split("@")[0], auth_provider="google", google_sub=google_sub, language_preference="en", password_hash=None)
        db.session.add(user)
    else:
        user.google_sub = google_sub
        user.auth_provider = "local+google" if user.password_hash else "google"
        user.display_name = user.display_name or profile.get("name") or email.split("@")[0]
    db.session.commit()
    record_login(user)
    return user


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "career-copilot", "version": "3.0.0", "timestamp": utc_now()})


@app.get("/api/meta")
def metadata():
    return jsonify({
        "name": "Career Copilot",
        "description": "An explainable bilingual AI assistant for learning, graduation projects, and career preparation.",
        "supported_languages": list(language_service.supported_languages),
        "features": ["secure authentication", "Google OAuth", "password recovery", "private conversation history", "advanced analytics dashboard", "intent classification", "feedback loop", "REST API", "real-time events"],
        "google_oauth_enabled": google_configured(),
    })


@app.post("/api/auth/register")
def register():
    payload, error = validate_registration(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    if User.query.filter(func.lower(User.email) == payload["email"]).first():
        return jsonify({"error": "An account with this email already exists"}), 409
    user = User(id=str(uuid.uuid4()), email=payload["email"], display_name=payload["display_name"], password_hash=generate_password_hash(payload["password"]), auth_provider="local", language_preference="en")
    db.session.add(user)
    db.session.commit()
    record_login(user)
    return jsonify({"message": "Account created", "user": user.to_dict()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = User.query.filter(func.lower(User.email) == email).first()
    if user is None or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    record_login(user)
    return jsonify({"message": "Signed in", "user": user.to_dict()})


@app.get("/api/auth/google")
def google_start():
    if not google_configured():
        return jsonify({"error": "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."}), 503
    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state
    params = {"client_id": os.getenv("GOOGLE_CLIENT_ID"), "redirect_uri": google_redirect_uri(), "response_type": "code", "scope": "openid email profile", "state": state, "access_type": "online", "prompt": "select_account"}
    return redirect(f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")


@app.get("/api/auth/google/callback")
def google_callback():
    if request.args.get("error"):
        return redirect("/?auth_error=Google+sign-in+was+cancelled")
    state = request.args.get("state")
    if not state or not secrets.compare_digest(state, session.pop("google_oauth_state", "")):
        return jsonify({"error": "Invalid OAuth state"}), 400
    code = request.args.get("code")
    if not code or not google_configured():
        return jsonify({"error": "Google OAuth is not configured or code is missing"}), 400
    try:
        token_response = requests.post(GOOGLE_TOKEN_ENDPOINT, data={"code": code, "client_id": os.getenv("GOOGLE_CLIENT_ID"), "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"), "redirect_uri": google_redirect_uri(), "grant_type": "authorization_code"}, timeout=10)
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        profile_response = requests.get(GOOGLE_USERINFO_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
        profile_response.raise_for_status()
        login_google_user(profile_response.json())
        return redirect("/")
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Google OAuth failed: %s", exc)
        return redirect("/?auth_error=Google+sign-in+failed")


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Signed out"})


@app.get("/api/auth/me")
@login_required
def me(user):
    return jsonify({"authenticated": True, "user": user.to_dict()})


@app.post("/api/auth/request-reset")
def request_reset():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    generic = {"message": "If an account exists for that email, a reset link will be sent shortly."}
    if not EMAIL_PATTERN.match(email):
        return jsonify(generic), 202
    user = User.query.filter(func.lower(User.email) == email).first()
    if user and user.password_hash:
        now = utc_datetime()
        PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).update({"used_at": now})
        raw_token = secrets.token_urlsafe(48)
        token = PasswordResetToken(user_id=user.id, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=now + timedelta(minutes=30))
        db.session.add(token)
        db.session.commit()
        try:
            send_reset_email(user, raw_token)
        except (OSError, smtplib.SMTPException) as exc:
            logger.warning("Reset email delivery failed: %s", exc)
    return jsonify(generic), 202


@app.post("/api/auth/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    raw_token = str(data.get("token", ""))
    error = validate_password(data.get("password"), data.get("confirm_password"))
    if not raw_token or error:
        return jsonify({"error": error or "A valid reset token is required"}), 400
    token = PasswordResetToken.query.filter_by(token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), used_at=None).first()
    if token is None or as_aware(token.expires_at) < utc_datetime():
        return jsonify({"error": "Reset token is invalid or expired"}), 400
    token.user.password_hash = generate_password_hash(str(data["password"]))
    token.user.auth_provider = "local+google" if token.user.google_sub else "local"
    token.used_at = utc_datetime()
    db.session.commit()
    return jsonify({"message": "Password reset successfully. Please sign in with your new password."})


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
        conversation = Conversation(user=user, message=message, response=result.response, language=language, intent=result.intent, confidence=result.confidence, sentiment=result.sentiment)
        db.session.add(conversation)
        db.session.commit()
        return jsonify({"response": result.response, "language": language, "conversation_id": conversation.id, "intent": result.intent, "confidence": result.confidence, "sentiment": result.sentiment, "timestamp": conversation.timestamp.isoformat()})
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
    conversation_id, rating = data.get("conversation_id"), data.get("rating")
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


def build_dashboard(user, days):
    since = utc_datetime() - timedelta(days=days)
    conversations = Conversation.query.filter(Conversation.user_id == user.id, Conversation.timestamp >= since).order_by(Conversation.timestamp.asc()).all()
    feedbacks = Feedback.query.filter(Feedback.user_id == user.id, Feedback.timestamp >= since).all()
    intent_breakdown, language_breakdown, daily_activity, hourly_activity = {}, {}, {}, {}
    for item in conversations:
        intent_breakdown[item.intent] = intent_breakdown.get(item.intent, 0) + 1
        language_breakdown[item.language] = language_breakdown.get(item.language, 0) + 1
        local_dt = as_aware(item.timestamp)
        day_key, hour_key = local_dt.strftime("%Y-%m-%d"), str(local_dt.hour)
        daily_activity[day_key] = daily_activity.get(day_key, 0) + 1
        hourly_activity[hour_key] = hourly_activity.get(hour_key, 0) + 1
    positive, negative = sum(1 for f in feedbacks if f.rating == 1), sum(1 for f in feedbacks if f.rating == 0)
    return {"period_days": days, "total_messages": len(conversations), "average_confidence": round(sum(c.confidence or 0 for c in conversations) / len(conversations), 3) if conversations else 0, "feedback": {"positive": positive, "negative": negative, "total": positive + negative}, "satisfaction_rate": round(positive / (positive + negative), 3) if positive + negative else None, "intent_breakdown": dict(sorted(intent_breakdown.items(), key=lambda pair: pair[1], reverse=True)), "language_breakdown": language_breakdown, "daily_activity": dict(sorted(daily_activity.items())), "hourly_activity": dict(sorted(hourly_activity.items(), key=lambda pair: int(pair[0]))), "active_days": len(daily_activity), "top_intent": max(intent_breakdown, key=intent_breakdown.get) if intent_breakdown else None}


@app.get("/api/analytics")
@login_required
def analytics(user):
    days = min(max(request.args.get("days", 30, type=int), 1), 90)
    return jsonify({"user_id": user.id, **build_dashboard(user, days)})


@app.get("/api/analytics/dashboard")
@login_required
def analytics_dashboard(user):
    days = min(max(request.args.get("days", 30, type=int), 1), 90)
    return jsonify(build_dashboard(user, days))


@app.post("/api/translate")
def translate_text():
    data = request.get_json(silent=True) or {}
    text_value, target = str(data.get("text", "")).strip(), str(data.get("target_language", "en")).lower()
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
    emit("connected", {"message": "Connected to Career Copilot", "version": "3.0.0"})


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Realtime client disconnected")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("DEBUG", "false").lower() == "true", allow_unsafe_werkzeug=True)
