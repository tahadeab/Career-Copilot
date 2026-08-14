# Career Copilot — Setup and Deployment Guide

This guide describes the supported local setup and the configuration required for email recovery and Google OAuth. It intentionally documents only behavior implemented in the current repository.

## 1. Prerequisites

Use Python 3.10 or newer, Git, and optionally Docker. A local SQLite database is sufficient for development. PostgreSQL is recommended for a multi-user production deployment.

## 2. Local installation

```bash
git clone https://github.com/tahadeab/Career-Copilot.git
cd Career-Copilot
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp env.example .env
python app.py
```

Open [http://localhost:5000](http://localhost:5000). The application initializes the default SQLite database automatically. Do not commit `.env` or local database files.

## 3. Environment configuration

The minimum local configuration is:

```dotenv
SECRET_KEY=replace-with-a-long-random-value
DEBUG=true
DATABASE_URL=sqlite:///career_copilot.db
APP_BASE_URL=http://localhost:5000
```

For production, use a secret manager, set `DEBUG=false`, use HTTPS, and configure a PostgreSQL connection string through `DATABASE_URL`.

## 4. Email password recovery

The reset endpoint works without SMTP for local development. In that mode, the generated reset link is written to the application log. To send real messages, configure an SMTP provider:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
MAIL_FROM=no-reply@example.com
APP_BASE_URL=https://your-domain.example
```

The recovery flow generates a random token, stores only its SHA-256 hash, expires it after 30 minutes, and marks it as used after a successful reset. The request endpoint intentionally returns a generic response for both existing and unknown email addresses.

## 5. Google OAuth

Create a Web application OAuth client in Google Cloud Console. Add this exact local redirect URI:

```text
http://localhost:5000/api/auth/google/callback
```

Then configure:

```dotenv
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

The application requests `openid email profile`, validates the OAuth `state`, retrieves the identity through Google's user-info endpoint, and creates or links a local user. Access tokens are not stored. If the three variables are missing, the Google login option remains safely unavailable.

## 6. API smoke checks

Start the application first, then run:

```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/meta
curl http://localhost:5000/api/suggestions
```

Expected health output includes `"status":"healthy"`. The metadata response reports the application version and whether Google OAuth is enabled.

## 7. Authentication examples

Create an account:

```bash
curl -i -c cookies.txt -X POST http://localhost:5000/api/auth/register \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"demo@example.com","display_name":"Demo User","password":"SecurePass123!"}'
```

Login and use the authenticated session:

```bash
curl -i -c cookies.txt -X POST http://localhost:5000/api/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"demo@example.com","password":"SecurePass123!"}'

curl -b cookies.txt http://localhost:5000/api/auth/me
```

Create a private conversation:

```bash
curl -b cookies.txt -X POST http://localhost:5000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"message":"How can I improve my CV?","language":"en"}'
```

Read the current user's dashboard:

```bash
curl -b cookies.txt 'http://localhost:5000/api/analytics/dashboard?days=30'
```

The API derives ownership from the session and does not trust a client-supplied `user_id`.

## 8. Tests and code quality

```bash
pytest -q
python -m py_compile app.py src/database/models.py
```

The test suite covers account creation, password hashing, session protection, ownership isolation, feedback ownership, reset-token single use and expiry behavior, analytics time series, language detection, and safe behavior when Google OAuth is not configured.

## 9. Docker

The repository includes a Dockerfile and a Compose file as starting points for local container execution. Review the environment values before using them outside development:

```bash
docker compose up --build
```

For a production service, place the application behind an HTTPS-capable reverse proxy and use a production WSGI server. The development `python app.py` command is not a production process manager.

## 10. Production hardening checklist

Before deployment, set a strong secret key, enable HTTPS, mark session cookies secure, configure exact CORS origins, add CSRF protection for cross-origin state-changing requests, rate-limit login and reset endpoints, use a managed PostgreSQL database, use a secrets manager for SMTP and OAuth credentials, configure structured logs, and introduce formal migrations such as Alembic.

These controls are deployment recommendations, not claims that every control is already enabled in the local demo.

## References

1. [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
2. [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
3. [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)

## License

MIT License. See [LICENSE.md](LICENSE.md).
