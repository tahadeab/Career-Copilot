#!/usr/bin/env python3
"""
Test script to verify Flask-SQLAlchemy setup is working correctly.
This script tests the database initialization and table creation.
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_database_setup():
    """Test the database setup and table creation."""
    try:
        # Create a test Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_chatbot.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Import and initialize the database
        from src.database.models import db
        db.init_app(app)
        
        # Test table creation
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test that we can query the tables
            from src.database.models import User, Conversation, Feedback, TrainingData
            
            # Check if tables exist by trying to count records
            user_count = User.query.count()
            conversation_count = Conversation.query.count()
            feedback_count = Feedback.query.count()
            training_data_count = TrainingData.query.count()
            
            print(f"✅ Database queries working:")
            print(f"   - Users: {user_count} records")
            print(f"   - Conversations: {conversation_count} records")
            print(f"   - Feedback: {feedback_count} records")
            print(f"   - Training Data: {training_data_count} records")
            
            # Clean up test database
            db.drop_all()
            print("Test database cleaned up successfully!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise AssertionError(f"Database setup failed: {e}") from e

if __name__ == "__main__":
    print("Testing Flask-SQLAlchemy setup...")
    test_database_setup()
    print("\nAll tests passed! Flask-SQLAlchemy setup is working correctly.")
    sys.exit(0)