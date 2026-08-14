# Career Copilot Architecture

## 1. System purpose

Career Copilot is a Flask-based, bilingual career-guidance application. It provides explainable responses for learning, graduation-project, CV, interview, and portfolio questions. The current runtime is intentionally **offline-friendly and deterministic**: it classifies intent, detects language, estimates sentiment, and selects a response policy without pretending that an external generative model is configured.

The platform also provides private accounts, password recovery, optional Google OAuth, user-owned conversation history, response feedback, and a user-scoped analytics dashboard.

## 2. Runtime architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ Browser                                                      │
│ templates/index.html                                         │
│ Auth forms · Chat workspace · History · Analytics dashboard  │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP / JSON + session cookie
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Flask application: app.py                                   │
│                                                              │
│ Public endpoints                                              │
│ health · meta · suggestions · auth register/login/reset      │
│                                                              │
│ Authenticated endpoints                                       │
│ auth/me · logout · chat · conversations · feedback           │
│ analytics/dashboard · translation                            │
│                                                              │
│ External auth endpoints                                       │
│ Google OAuth authorize → callback                             │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
                ▼                              ▼
┌───────────────────────────────┐  ┌───────────────────────────┐
│ Domain services                │  │ External services         │
│ ChatbotService                 │  │ SMTP: password recovery   │
│ LanguageService                │  │ Google OAuth 2.0          │
│ FeedbackService                │  │                           │
│ TrainingService (data helper)  │  │ Optional; disabled safely │
└───────────────┬───────────────┘  └───────────────────────────┘
                │ SQLAlchemy ORM
                ▼
┌──────────────────────────────────────────────────────────────┐
│ Relational database                                          │
│ SQLite by default; DATABASE_URL can point to PostgreSQL      │
│ users · password_reset_tokens · conversations · feedback     │
│ training_data                                                 │
└──────────────────────────────────────────────────────────────┘
```

## 3. Request and ownership flow

Every state-changing request is processed by Flask, validated as JSON, and then handled using the authenticated user stored in the server-side session. A client cannot select another user's identity by sending a different `user_id`; ownership is derived from `session["user_id"]`.

```text
Request
  │
  ├─ Public route? ── yes ──> input validation ──> service / database
  │
  └─ Protected route
       │
       ├─ session user exists? ── no ──> 401
       │
       ├─ load current User
       │
       ├─ query/write only records owned by current user
       │
       └─ return JSON response
```

For chat requests, the application detects the language, classifies an intent, calculates confidence and sentiment signals, generates an explainable response, stores the conversation with the current user's ID, and returns the result. Feedback is accepted only when the referenced conversation belongs to the current user.

## 4. Authentication architecture

### Local authentication

Registration validates the email and password policy, hashes the password with Werkzeug, and stores only the hash. Login compares the submitted password against the stored hash, rotates the session, and records login metadata. Logout clears the session.

### Password recovery

The reset flow follows a single-use token model. A cryptographically random token is generated, only its SHA-256 hash is stored in the database, and the token expires after 30 minutes. The request endpoint returns a generic response whether or not the email exists. SMTP delivery is optional in local development; when SMTP is not configured, the reset URL is logged for development visibility.

```text
Request reset
  → generic response
  → random token generated
  → token hash stored with expiry
  → SMTP email or development log
  → token submitted once
  → password updated and token marked used
```

### Google OAuth 2.0

Google OAuth is optional and uses the server-side authorization-code flow. The application creates a state value, redirects the user to Google with the minimal `openid email profile` scopes, validates the returned state, exchanges the authorization code, retrieves the identity, and links or creates a local user. Google access tokens are not persisted. If OAuth secrets are absent, the feature reports that it is unavailable instead of failing silently.

## 5. Database model

```text
User 1 ─────────────── * Conversation
 │                         │
 │                         └──── 0..1 Feedback
 │
 ├──────────────────── * PasswordResetToken
 │
 └──────────────────── * Feedback

TrainingData is independent reference data used by the training/feedback helpers.
```

| Entity | Responsibility | Important fields |
| --- | --- | --- |
| `User` | Local and external identity | `email`, `password_hash`, `auth_provider`, `google_sub`, login metadata |
| `PasswordResetToken` | One-time recovery token state | `token_hash`, `expires_at`, `used_at`, `user_id` |
| `Conversation` | Private message/response record | `user_id`, message, response, language, intent, confidence, sentiment, timestamp |
| `Feedback` | User-owned response rating | `conversation_id`, `user_id`, rating, comment, timestamp |
| `TrainingData` | Curated examples for future improvement | intent, text, language, verification flags |

Indexes support email and Google identity lookup, reset-token expiry queries, and user/time conversation queries. Database initialization includes a lightweight compatibility step for older local SQLite files; production deployments should use a formal migration tool before schema changes become frequent.

## 6. Analytics architecture

`GET /api/analytics/dashboard?days=30` builds metrics only from the current user's conversations and feedback. The period is bounded to 1–90 days. The response contains aggregate cards and chart-ready series:

| Metric group | Examples |
| --- | --- |
| Volume | total messages, active days |
| Quality | average confidence, helpful ratings, satisfaction rate |
| Distribution | top intent, intent counts, language counts |
| Time series | daily message activity, hourly activity |
| Usage context | latest activity and authenticated account metadata |

No global analytics are exposed through the user dashboard. If an administrative analytics layer is added later, it should use a separate authorization boundary and separate endpoints.

## 7. API surface

| Area | Routes |
| --- | --- |
| Platform | `GET /`, `GET /api/health`, `GET /api/meta`, `GET /api/suggestions` |
| Local auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` |
| Recovery | `POST /api/auth/request-reset`, `POST /api/auth/reset-password` |
| Google OAuth | `GET /api/auth/google`, `GET /api/auth/google/callback` |
| Private work | `POST /api/chat`, `GET /api/conversations`, `POST /api/feedback`, `GET /api/analytics/dashboard` |
| Language | `POST /api/translate` |

## 8. Security boundaries and deployment notes

The application uses HttpOnly sessions, password hashing, ownership-scoped queries, token hashing, token expiry, OAuth state validation, generic recovery responses, and input validation. Production deployment should additionally enable HTTPS, a strong secret key, secure cookie settings, CSRF protection for cross-origin state-changing requests, rate limiting for login and recovery, a managed secrets store, structured logging, and formal database migrations.

The included Docker configuration is a starting point rather than proof of production readiness. SQLite is suitable for local development and demonstrations; PostgreSQL is the preferred production database for concurrent workloads.

## 9. Source of truth

The implementation in `app.py`, `src/database/models.py`, `src/services/`, `templates/index.html`, `tests/test_app.py`, `README.md`, and `env.example` is authoritative. Historical documents that describe FAISS, DialoGPT, Socket.IO events, or unimplemented retrieval/generative services are no longer considered part of the current architecture.

## References

1. [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
2. [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
3. [Flask Documentation](https://flask.palletsprojects.com/)
4. [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
5. [Werkzeug Security Utilities](https://werkzeug.palletsprojects.com/en/latest/utils/#module-werkzeug.security)

## License

This project is released under the MIT License. See [LICENSE.md](LICENSE.md).
