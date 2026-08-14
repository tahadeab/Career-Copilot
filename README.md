# Career Copilot

> An explainable bilingual career-guidance assistant that helps students and early-career builders turn questions into practical next steps.

Career Copilot is a portfolio-ready Flask application for private, measurable career guidance. Users can create an account, sign in with a password or Google, ask questions in English or Arabic, inspect intent and confidence signals, rate responses, recover their password through email, and review a personal analytics dashboard.

## Product capabilities

| Capability | Implementation |
| --- | --- |
| Private accounts | SQLAlchemy-backed users with server-side HttpOnly sessions and user-scoped data access |
| Password security | Werkzeug one-way password hashes, minimum password policy, single-use reset tokens hashed in the database |
| External identity | Optional Google OAuth 2.0 authorization-code flow with state validation and verified email identity |
| Bilingual guidance | English and Arabic responses with automatic language detection, RTL support, and controlled translation |
| Explainable responses | Intent label, confidence score, and sentiment signal returned for every message |
| Advanced analytics | Period selector, message volume, active days, average confidence, top intent, intent mix, language mix, feedback, and daily/hourly activity |
| Feedback loop | Helpful / needs-work ratings with ownership checks and satisfaction rate |
| Professional UI | Responsive workspace, dashboard cards, inline charts, dark mode, suggestions, and account controls |
| API-first design | Health, metadata, authentication, recovery, Google OAuth, chat, history, analytics, feedback, and translation endpoints |
| Quality assurance | Ten integration tests covering auth, ownership isolation, reset tokens, analytics, validation, and OAuth configuration |

## Architecture

```text
Browser UI
   │
   ├── Authentication UI: local login, password reset, Google OAuth redirect
   ├── Private chat workspace and analytics dashboard
   └── REST API requests with an HttpOnly session cookie

Flask application
   ├── Auth flows: local credentials, reset tokens, Google authorization-code callback
   ├── ChatbotService: intent classification, confidence, sentiment, response policy
   ├── Analytics service: user-scoped time-series and quality metrics
   └── SQLAlchemy models: users, reset tokens, conversations, feedback, training data
   │
SQLite by default (PostgreSQL-compatible DATABASE_URL supported)
```

The current response engine is deliberately explainable and offline-friendly. It uses normalized phrase matching and returns a `ChatResult` with `response`, `intent`, `confidence`, and `sentiment`. A hosted LLM or RAG layer can be added behind the same service boundary later.

## Quick start

```bash
git clone https://github.com/tahadeab/Career-Copilot.git
cd Career-Copilot
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp env.example .env
python app.py
```

Open [http://localhost:5000](http://localhost:5000). The default SQLite database is created automatically as `career_copilot.db`.

## Authentication and password recovery

Local registration and login are available through the following endpoints:

| Endpoint | Purpose | Access |
| --- | --- | --- |
| `POST /api/auth/register` | Create an account with email, display name, and password | Public |
| `POST /api/auth/login` | Start a secure server-side session | Public |
| `POST /api/auth/logout` | Clear the current session | Public |
| `GET /api/auth/me` | Return the current authenticated user | Authenticated |
| `POST /api/auth/request-reset` | Request a reset email with a generic anti-enumeration response | Public |
| `POST /api/auth/reset-password` | Consume a single-use, 30-minute reset token | Public |

Reset tokens are generated with the Python secrets module, stored as SHA-256 hashes, expire after 30 minutes, and are marked as used after a successful reset. SMTP is optional for local development; without SMTP configuration, the reset URL is written to the application log rather than sent over email.

## Google OAuth setup

Create a Web application OAuth client in Google Cloud Console and add this exact redirect URI:

```text
http://localhost:5000/api/auth/google/callback
```

Then configure the environment:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

The application requests only `openid email profile`, creates or links the verified Google identity, validates the OAuth `state` value, and does not store Google access tokens. In production, use HTTPS, a strong secret key, exact production redirect URIs, and a managed secrets service.

## SMTP setup

For real password-reset delivery, configure an SMTP provider without committing credentials:

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
MAIL_FROM=no-reply@example.com
APP_BASE_URL=https://your-domain.example
```

## Analytics API

`GET /api/analytics/dashboard?days=30` returns the signed-in user's analytics for a period from 1 to 90 days. The response includes total messages, active days, average confidence, feedback totals, satisfaction rate, intent and language breakdowns, daily activity, hourly activity, and the top intent. The endpoint never accepts a user ID from the client and derives ownership from the current server session.

## Other API examples

```bash
# Health
curl http://localhost:5000/api/health

# Authenticated chat: use a browser session or a cookie jar after login
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message":"How can I improve my CV?","language":"en"}'
```

## Testing and code quality

```bash
pytest -q
python -m py_compile app.py src/database/models.py
```

The automated suite validates account creation, password hashing behavior, session protection, conversation ownership isolation, feedback ownership, reset-token single use, generic reset responses, dashboard time series, Arabic detection, and disabled Google OAuth configuration. A production deployment should also add CSRF protection for cross-origin state-changing requests, rate limiting for login and reset endpoints, HTTPS, and a formal migration tool.

## CV-ready project description

**Career Copilot — Secure Explainable Career Guidance Platform:** Built and tested a Flask-based bilingual career assistant with SQLAlchemy user isolation, secure password hashing and single-use email recovery tokens, optional Google OAuth 2.0, explainable intent and confidence signals, user-scoped analytics dashboards, feedback-based satisfaction metrics, responsive RTL-aware UI, REST APIs, and automated integration tests.

## References

The OAuth implementation follows Google's server-side web application authorization-code guidance: [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server). Password recovery design follows [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

## License

This project is released under the MIT License. See [LICENSE.md](LICENSE.md).
