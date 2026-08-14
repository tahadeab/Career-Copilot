"""Centralized optional configuration helpers for Career Copilot.

The Flask application currently reads the same environment variables directly in
``app.py`` so that the standalone entry point remains simple. This module keeps
an importable configuration contract for deployments and tooling without
advertising model, FAISS, or rate-limit settings that are not runtime features.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration values shared by local and deployment tooling."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-development-secret")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///career_copilot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    SUPPORTED_LANGUAGES = ("en", "ar")
    DEFAULT_LANGUAGE = "en"

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback"
    )


class DevelopmentConfig(Config):
    """Local development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Configuration used by automated tests."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Deployment configuration with explicit secret requirements."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if not os.getenv("SECRET_KEY"):
            raise ValueError("SECRET_KEY must be set in production")
        if not os.getenv("DATABASE_URL"):
            raise ValueError("DATABASE_URL must be set in production")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Return the configuration class selected by ``FLASK_ENV``."""

    return config.get(os.getenv("FLASK_ENV", "development"), DevelopmentConfig)
