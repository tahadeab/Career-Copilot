# Career Copilot — Project Overview

## Product definition

Career Copilot is a bilingual English/Arabic career-guidance assistant built for students, graduation-project teams, and early-career developers. It converts questions about learning, CVs, interviews, portfolios, and project planning into structured next steps while exposing intent, confidence, and sentiment signals for explainability.

The application is intentionally designed as a portfolio-quality foundation. The current response engine is deterministic and offline-friendly, which makes local demonstrations reliable and keeps the product honest about which external AI services are configured. A hosted LLM or retrieval system can be added later behind the existing service boundary.

## Current capabilities

| Area | Implemented behavior |
| --- | --- |
| Conversation guidance | Classifies common career and learning intents and generates bilingual policy-based responses |
| Explainability | Returns intent, confidence, and sentiment signals with every response |
| User accounts | Local registration, login, logout, and authenticated sessions |
| Private data | Conversations, feedback, and analytics are scoped to the authenticated user |
| Password recovery | Hashed, single-use, expiring reset tokens with SMTP or development-log delivery |
| External identity | Optional Google OAuth 2.0 authorization-code flow with state validation |
| Analytics | User-scoped volume, quality, distribution, and time-series dashboard data |
| Feedback | Helpful/needs-work ratings and comments with ownership checks |
| Interface | Responsive English-first UI, Arabic support, RTL handling, dark mode, suggestions, history, and dashboard charts |
| API | Flask JSON endpoints for platform, auth, recovery, OAuth, chat, history, feedback, analytics, and translation |

## Architecture summary

```text
Browser UI
  → Flask routes and session guard
  → ChatbotService / LanguageService / FeedbackService
  → SQLAlchemy models and relational database

Optional boundaries:
  SMTP for recovery email
  Google OAuth 2.0 for external identity
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for request flows, data ownership, database relationships, security boundaries, and deployment guidance.

## Repository structure

```text
Career-Copilot/
├── app.py                         Flask application and API routes
├── config.py                      Environment and runtime configuration
├── requirements.txt               Runtime and test dependencies
├── env.example                    Safe configuration template
├── Dockerfile                     Container starting point
├── docker-compose.yml             Local container orchestration
├── README.md                      Primary project documentation
├── ARCHITECTURE.md                Current architecture source of truth
├── SETUP.md                       Local and production-oriented setup guide
├── DATABASE_REFACTOR.md           Historical database refactor notes
├── LICENSE.md                     MIT license
├── src/
│   ├── database/models.py         SQLAlchemy entities and relationships
│   ├── services/chatbot_service.py Explainable response engine
│   ├── services/language_service.py Language detection and translation boundary
│   ├── services/feedback_service.py Feedback helpers
│   ├── services/training_service.py Training-data helper boundary
│   └── utils/logger.py             Application logging
├── templates/index.html            Frontend workspace
├── tests/test_app.py               Integration and ownership tests
├── test_db_setup.py                Database initialization test
├── docs/                           Security research and presentation outline
└── presentation/                   Editable slide project
```

## Data model

The relational model is intentionally compact and focused on product behavior.

| Model | Role |
| --- | --- |
| `User` | Stores local identity, optional Google identity, language preference, and login metadata |
| `PasswordResetToken` | Stores only a hash of a time-limited, single-use recovery token |
| `Conversation` | Stores a user's message, response, language, intent, confidence, sentiment, and timestamp |
| `Feedback` | Stores a user's rating and optional comment for their conversation |
| `TrainingData` | Stores curated text examples for future feedback/training workflows |

## Main API groups

| Group | Endpoints |
| --- | --- |
| Platform | `/api/health`, `/api/meta`, `/api/suggestions` |
| Authentication | `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me` |
| Recovery | `/api/auth/request-reset`, `/api/auth/reset-password` |
| Google | `/api/auth/google`, `/api/auth/google/callback` |
| Private workspace | `/api/chat`, `/api/conversations`, `/api/feedback`, `/api/analytics/dashboard` |
| Language | `/api/translate` |

## Quality status

The automated suite covers registration, password hashing, login protection, private conversation history, feedback ownership, reset-token behavior, analytics periods and series, Arabic detection, and disabled Google OAuth configuration. Run `pytest -q` before submitting a change.

## Deliberate non-features

The repository does not currently ship a FAISS index, sentence-transformer model, DialoGPT model, Socket.IO event protocol, or production-grade background training scheduler. Those ideas may appear in historical documents from the original chatbot prototype, but they are not part of the current runtime and must not be presented as implemented capabilities.

## Professional value

This project demonstrates full-stack Python development, secure authentication, database ownership controls, third-party OAuth integration, email recovery, explainable conversational logic, analytics design, frontend integration, API design, testing, and technical documentation in a single coherent product.

## References

1. [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
2. [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

## License

Career Copilot is distributed under the MIT License. See [LICENSE.md](LICENSE.md).
