# Career Copilot — Executive Project Summary

## Executive summary

Career Copilot is a secure, bilingual career-guidance web application for students and early-career developers. It combines a Flask REST API, SQLAlchemy persistence, a responsive browser workspace, explainable response logic, private conversation history, password recovery, optional Google OAuth, feedback collection, and a user-scoped analytics dashboard.

The project is intentionally honest about its runtime. Its current conversational engine is lightweight, deterministic, and offline-friendly. It provides a stable product experience without requiring a paid AI provider or a downloaded language model. The service boundary leaves room for a hosted LLM or retrieval-augmented generation layer in a future iteration.

## Problem and solution

Students often receive generic career advice without knowing why a response was produced or how their progress changes over time. Career Copilot addresses this by combining guided conversational responses with visible intent and confidence signals, a private history, response feedback, and analytics that help a user understand their own usage patterns.

## Technical highlights

| Capability | Evidence in the codebase |
| --- | --- |
| Secure identity | Werkzeug password hashes, server-side sessions, optional Google OAuth state validation |
| Recovery security | SHA-256 token hashes, 30-minute expiry, single-use reset behavior, generic request responses |
| Data isolation | User ID comes from the authenticated session; conversation and feedback queries enforce ownership |
| Analytics | User-scoped aggregations for volume, confidence, intent, languages, ratings, and time series |
| Explainable AI behavior | Intent, confidence, sentiment, and response policy are returned explicitly |
| API design | JSON endpoints separated into platform, auth, recovery, OAuth, private work, and language groups |
| Testing | Pytest integration tests for auth, isolation, recovery, analytics, validation, and configuration |
| Documentation | README, architecture guide, setup guide, security research notes, and presentation project |

## User journey

```text
Create account or use Google
        ↓
Authenticate and open private workspace
        ↓
Ask a career or learning question
        ↓
Receive bilingual explainable guidance
        ↓
Save private conversation and optionally rate it
        ↓
Review personal analytics and usage patterns
```

## Data and privacy boundaries

The application treats the authenticated user as the owner of conversations, feedback, and analytics. Passwords are never stored in plaintext. Password recovery stores only a token hash. Google access tokens are not persisted. The default development database is SQLite, while the application accepts a PostgreSQL-compatible `DATABASE_URL` for a stronger deployment foundation.

## Development status

The following areas are implemented and tested:

- Local registration, login, logout, and session discovery.
- Password reset request and password update flows.
- Optional Google OAuth authorization-code flow.
- Private conversations, feedback, and analytics.
- English and Arabic language detection and controlled translation behavior.
- Responsive frontend with account controls, history, suggestions, dashboard cards, and charts.
- Health and metadata endpoints for operational checks.

The following areas remain future enhancements rather than current claims: CSRF protection, rate limiting, formal Alembic migrations, background job processing, hosted LLM/RAG integration, admin analytics, and production observability.

## Suggested CV entry

> **Career Copilot — Secure Explainable Career Guidance Platform:** Built a Flask and SQLAlchemy application with private user accounts, password hashing, single-use email recovery tokens, optional Google OAuth 2.0, ownership-scoped conversation history, explainable bilingual intent/confidence signals, user analytics dashboards, feedback metrics, responsive RTL-aware UI, REST APIs, and automated integration tests.

## Project references

- [README](README.md) — installation, API usage, and environment configuration.
- [ARCHITECTURE](ARCHITECTURE.md) — current runtime and security architecture.
- [SETUP](SETUP.md) — local development and deployment preparation.
- [Security research](docs/security-research.md) — Google and OWASP design references.

## License

MIT License. See [LICENSE.md](LICENSE.md).
