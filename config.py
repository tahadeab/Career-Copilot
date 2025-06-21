"""
Configuration settings for Smart AI Chatbot
Centralized configuration management for all application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///chatbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # AI/ML Model Configuration
    SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
    GENERATIVE_MODEL = os.getenv('GENERATIVE_MODEL', 'microsoft/DialoGPT-medium')
    SENTIMENT_MODEL = os.getenv('SENTIMENT_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
    
    # FAISS Configuration
    FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'models/faiss_index')
    FAISS_DIMENSION = int(os.getenv('FAISS_DIMENSION', '384'))
    FAISS_NPROBE = int(os.getenv('FAISS_NPROBE', '10'))
    
    # Language Processing
    SUPPORTED_LANGUAGES = ['en', 'ar']
    DEFAULT_LANGUAGE = 'en'
    TRANSLATION_SERVICE = os.getenv('TRANSLATION_SERVICE', 'google')
    
    # Training Configuration
    TRAINING_DATA_PATH = os.getenv('TRAINING_DATA_PATH', 'data/training')
    MODEL_SAVE_PATH = os.getenv('MODEL_SAVE_PATH', 'models')
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.7'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/chatbot.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10MB'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Performance Configuration
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '100'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
    
    # Security Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))
    
    # Feedback Configuration
    FEEDBACK_ENABLED = os.getenv('FEEDBACK_ENABLED', 'True').lower() == 'true'
    MIN_FEEDBACK_RATING = int(os.getenv('MIN_FEEDBACK_RATING', '4'))
    FEEDBACK_COOLDOWN = int(os.getenv('FEEDBACK_COOLDOWN', '300'))
    
    # Training Pipeline Configuration
    TRAINING_SCHEDULE = os.getenv('TRAINING_SCHEDULE', 'weekly')  # daily, weekly, monthly
    MIN_TRAINING_SAMPLES = int(os.getenv('MIN_TRAINING_SAMPLES', '100'))
    MODEL_EVALUATION_THRESHOLD = float(os.getenv('MODEL_EVALUATION_THRESHOLD', '0.8'))
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH = os.getenv('KNOWLEDGE_BASE_PATH', 'data/knowledge_base')
    MAX_KNOWLEDGE_ENTRIES = int(os.getenv('MAX_KNOWLEDGE_ENTRIES', '10000'))
    KNOWLEDGE_UPDATE_INTERVAL = int(os.getenv('KNOWLEDGE_UPDATE_INTERVAL', '86400'))
    
    # Embedding Cache Configuration
    EMBEDDING_CACHE_ENABLED = os.getenv('EMBEDDING_CACHE_ENABLED', 'True').lower() == 'true'
    EMBEDDING_CACHE_SIZE = int(os.getenv('EMBEDDING_CACHE_SIZE', '10000'))
    EMBEDDING_CACHE_TTL = int(os.getenv('EMBEDDING_CACHE_TTL', '86400'))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chatbot_dev.db'
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chatbot_test.db'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Production security settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production performance settings
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '1000'))
    CACHE_TTL = int(os.getenv('CACHE_TTL', '7200'))

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    config_name = os.getenv('FLASK_ENV', 'default')
    return config.get(config_name, config['default']) 