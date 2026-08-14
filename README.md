# Career Copilot

> An explainable bilingual AI assistant that helps students and early-career builders turn questions into practical next steps.

Career Copilot is a portfolio-ready Flask application built around a clear product goal: make AI guidance useful, inspectable, and measurable. Instead of presenting a black-box demo, the project exposes the reasoning signals behind each response through intent classification, confidence, sentiment, persistent conversation history, and user feedback analytics.

## Why this project matters

The project demonstrates a complete product workflow rather than a single chatbot endpoint. A user can ask a question in English or Arabic, receive a topic-aware response, inspect the detected intent and confidence, rate the answer, and review quality metrics. The design is intentionally lightweight and offline-friendly, making it simple to run locally while leaving clean integration points for a hosted LLM, a translation provider, authentication, or a production database.

## Product capabilities

| Capability | Implementation |
| --- | --- |
| Bilingual interaction | English and Arabic responses with automatic language detection |
| Explainable responses | Intent label, confidence score, and sentiment signal returned for every message |
| Persistent history | SQLite by default with SQLAlchemy models and indexed conversation queries |
| Feedback loop | Helpful / needs-work ratings with upsert behavior and satisfaction rate |
| Analytics | Message totals, intent breakdown, feedback totals, and satisfaction rate |
| Professional UI | Responsive dashboard, dark mode, suggestions, status indicators, and RTL support |
| API-first design | Health, metadata, suggestions, chat, history, analytics, feedback, and translation endpoints |
| Real-time readiness | Flask-SocketIO connection events included for future streaming responses |
| Quality assurance | Pytest integration tests for core flows and validation behavior |

## Architecture

```text
Browser UI
   │
   ├── REST API /api/chat, /api/feedback, /api/analytics
   ├── Optional Socket.IO connection events
   │
Flask application
   ├── LanguageService: detection and controlled phrase translation
   ├── ChatbotService: intent classification, confidence, sentiment, response policy
   └── SQLAlchemy models: users, conversations, feedback, training data
   │
SQLite by default (PostgreSQL-compatible configuration supported)
```

The response engine is deliberately explainable. It uses normalized phrase matching for the current offline demo and returns a `ChatResult` object with `response`, `intent`, `confidence`, and `sentiment`. This separation makes it straightforward to replace or augment the engine with embeddings or a hosted generative model without rewriting the API or frontend.

## Quick start

```bash
git clone https://github.com/tahadeab/graduation-ai-chatbot.git
cd graduation-ai-chatbot
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp env.example .env             # optional; defaults work for local development
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in a browser. The default database is created automatically as `career_copilot.db`.

## API examples

Send a message:

```bash
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message":"How can I improve my CV?","user_id":"demo-user","language":"en"}'
```

The response contains the assistant answer, detected intent, confidence, sentiment, conversation ID, language, and timestamp. History is available at `/api/conversations/<user_id>`, while personal analytics are available at `/api/analytics/<user_id>`.

## Testing and code quality

Run the automated suite with:

```bash
pytest -q
python -m py_compile app.py src/database/models.py src/services/chatbot_service.py src/services/language_service.py
black --check app.py src tests
flake8 app.py src tests
```

## Configuration

The application reads environment variables through `.env`. `DATABASE_URL` can point to PostgreSQL in a deployment environment; `SECRET_KEY`, `PORT`, `DEBUG`, `LOG_LEVEL`, and `CORS_ORIGINS` are also supported. Never commit real secrets to the repository.

## CV-ready project description

**Career Copilot — Explainable Bilingual AI Assistant:** Built and tested a Flask-based AI assistant with English/Arabic language detection, intent classification, confidence and sentiment signals, persistent SQLAlchemy conversation history, feedback-driven satisfaction analytics, responsive RTL-aware UI, REST endpoints, and automated pytest coverage.

## Roadmap

The next production milestones are provider-backed generative responses with retrieval-augmented grounding, user authentication, database migrations, rate limiting, structured observability, and a multilingual evaluation dataset. These are intentionally documented as roadmap items rather than claimed features.

## License

This project is released under the MIT License. See [LICENSE.md](LICENSE.md).

## Authentication and private history

Career Copilot now includes account authentication backed by the application database. Users can create an account, sign in, sign out, and inspect their active session through the following endpoints:

| Endpoint | Purpose | Access |
| --- | --- | --- |
| `POST /api/auth/register` | Create an account with email, display name, and password | Public |
| `POST /api/auth/login` | Start a secure server-side session | Public |
| `POST /api/auth/logout` | Clear the current session | Authenticated |
| `GET /api/auth/me` | Return the current authenticated user | Authenticated |
| `GET /api/conversations` | Return only the signed-in user's history | Authenticated |
| `GET /api/analytics` | Return only the signed-in user's metrics | Authenticated |

Passwords are stored with Werkzeug's one-way password hashing utilities and are never returned by the API. The browser uses an `HttpOnly`, `SameSite=Lax` session cookie. Chat, conversation history, feedback, and analytics endpoints derive the user identity from the server session instead of trusting a client-supplied `user_id`. This prevents one account from reading or rating another account's conversations.

For deployments behind HTTPS, set `SESSION_COOKIE_SECURE=true` and provide a strong random `SECRET_KEY` through the environment. Existing SQLite databases are upgraded with the authentication columns when the application starts; production deployments should still use a dedicated migration tool as the schema evolves.
