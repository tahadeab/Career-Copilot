"""
Database models for Smart AI Chatbot
Defines all database tables and relationships.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance (to be bound to app later)
db = SQLAlchemy()


class User(db.Model):
    """User model for storing user information."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(100), primary_key=True)
    language_preference = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'language_preference': self.language_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Conversation(db.Model):
    """Conversation model for storing chat history."""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    feedback = db.relationship('Feedback', backref='conversation', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'language': self.language,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Feedback(db.Model):
    """Feedback model for storing user feedback on responses."""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 for positive, 0 for negative
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class TrainingData(db.Model):
    """Training data model for storing samples used for model training."""
    __tablename__ = 'training_data'
    
    id = db.Column(db.Integer, primary_key=True)
    intent = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    embedding = db.Column(db.Text, nullable=True)  # Stored as JSON string
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_for_training = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'intent': self.intent,
            'text': self.text,
            'language': self.language,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_for_training': self.used_for_training
        }
