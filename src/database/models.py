"""Database models for the Career Copilot chatbot."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def utc_now():
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(100), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    display_name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    language_preference = db.Column(db.String(10), default="en", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    conversations = db.relationship("Conversation", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "language_preference": self.language_preference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Conversation(db.Model):
    __tablename__ = "conversations"
    __table_args__ = (
        db.Index("ix_conversations_user_timestamp", "user_id", "timestamp"),
        db.Index("ix_conversations_language", "language"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="en", nullable=False)
    intent = db.Column(db.String(80), default="general", nullable=False)
    confidence = db.Column(db.Float, default=0.0, nullable=False)
    sentiment = db.Column(db.String(20), default="neutral", nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    feedback = db.relationship("Feedback", backref="conversation", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "response": self.response,
            "language": self.language,
            "intent": self.intent,
            "confidence": round(self.confidence or 0.0, 3),
            "sentiment": self.sentiment,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "feedback": self.feedback.rating if self.feedback else None,
        }


class Feedback(db.Model):
    __tablename__ = "feedback"
    __table_args__ = (db.UniqueConstraint("conversation_id", "user_id", name="uq_feedback_conversation_user"),)

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    user_id = db.Column(db.String(100), db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class TrainingData(db.Model):
    __tablename__ = "training_data"

    id = db.Column(db.Integer, primary_key=True)
    intent = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="en", nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    used_for_training = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "intent": self.intent,
            "text": self.text,
            "language": self.language,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "used_for_training": self.used_for_training,
        }
