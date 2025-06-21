"""
Smart AI Chatbot - Main Application
A self-learning bilingual chatbot system powered by NLP, Machine Learning, and feedback-driven continuous training.
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from typing import Any
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


# Import database models and db instance
from src.database.models import db, User, Conversation, Feedback, TrainingData
from src.services.chatbot_service import ChatbotService
from src.services.language_service import LanguageService
from src.services.feedback_service import FeedbackService
from src.services.training_service import TrainingService
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure Flask app with database settings
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# Initialize Flask-SQLAlchemy with the app
# This connects the db instance from models.py to the Flask app
db.init_app(app)

# Initialize services
chatbot_service = ChatbotService()
language_service = LanguageService()
feedback_service = FeedbackService()
training_service = TrainingService()

print("نوع app هو:", type(app))

@app.before_first_request
def create_tables():
    """Create database tables if they don't exist."""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests from the frontend."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        language = data.get('language', 'en')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Detect language if not specified
        if language == 'auto':
            detected_lang = language_service.detect_language(user_message)
            language = detected_lang
        
        # Get or create user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id, language_preference=language)
            db.session.add(user)
            db.session.commit()
        
        # Process message and get response
        response = chatbot_service.process_message(user_message, user_id, language)
        
        # Save conversation to database
        conversation = Conversation(
            user_id=user_id,
            message=user_message,
            response=response,
            language=language,
            timestamp=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'language': language,
            'conversation_id': conversation.id,
            'timestamp': conversation.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission for responses."""
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        rating = data.get('rating')  # 1 for positive, 0 for negative
        user_id = data.get('user_id')
        
        if not all([conversation_id, rating is not None, user_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Save feedback
        feedback = Feedback(
            conversation_id=conversation_id,
            rating=rating,
            user_id=user_id,
            timestamp=datetime.utcnow()
        )
        db.session.add(feedback)
        db.session.commit()
        
        # Process feedback for training
        feedback_service.process_feedback(conversation_id, rating)
        
        return jsonify({'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        logger.error(f"Error in feedback endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/conversations/<user_id>', methods=['GET'])
def get_conversations(user_id):
    """Get conversation history for a user."""
    try:
        conversations = Conversation.query.filter_by(user_id=user_id)\
            .order_by(Conversation.timestamp.desc())\
            .limit(50).all()
        
        conversation_list = []
        for conv in conversations:
            feedback = Feedback.query.filter_by(conversation_id=conv.id).first()
            conversation_list.append({
                'id': conv.id,
                'message': conv.message,
                'response': conv.response,
                'language': conv.language,
                'timestamp': conv.timestamp.isoformat(),
                'feedback': feedback.rating if feedback else None
            })
        
        return jsonify({'conversations': conversation_list})
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text between Arabic and English."""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        target_language = data.get('target_language', 'en')
        
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        translated_text = language_service.translate_text(text, target_language)
        
        return jsonify({
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language
        })
        
    except Exception as e:
        logger.error(f"Error in translation endpoint: {str(e)}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# WebSocket events for real-time chat
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Smart AI Chatbot'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat messages."""
    try:
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        language = data.get('language', 'en')
        
        if not user_message:
            emit('error', {'error': 'Message cannot be empty'})
            return
        
        # Process message
        response = chatbot_service.process_message(user_message, user_id, language)
        
        # Save conversation
        conversation = Conversation(
            user_id=user_id,
            message=user_message,
            response=response,
            language=language,
            timestamp=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Emit response
        emit('bot_response', {
            'response': response,
            'language': language,
            'conversation_id': conversation.id,
            'timestamp': conversation.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in WebSocket chat: {str(e)}")
        emit('error', {'error': 'Internal server error'})

if __name__ == '__main__':
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Smart AI Chatbot on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug) 