# Database Refactor Notes

## Purpose

This document records the migration from the original pure-SQLAlchemy prototype to the Flask-SQLAlchemy integration used by Career Copilot. It is a historical engineering note; the current schema and relationships are defined in `src/database/models.py`, and the current runtime configuration is described in [ARCHITECTURE.md](ARCHITECTURE.md).

## Original issue

The early prototype defined a declarative SQLAlchemy base while the Flask application expected a Flask-SQLAlchemy object. This created an initialization mismatch: the application attempted to call `init_app` on an object that was not a configured Flask-SQLAlchemy extension.

## Current implementation

The application now creates one shared extension instance:

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

The Flask application configures the database URI and initializes the extension:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///career_copilot.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
```

Models inherit from `db.Model` and use the extension's column, relationship, and foreign-key helpers.

## Current entities

| Entity | Purpose |
| --- | --- |
| `User` | Local identity, optional Google identity, language preference, and login metadata |
| `PasswordResetToken` | Hashed, expiring, single-use password recovery token |
| `Conversation` | User-owned message, response, and explainability metadata |
| `Feedback` | User-owned rating and optional comment |
| `TrainingData` | Curated examples for future training or response improvement |

The historical prototype mentioned `ModelVersion` and `EmbeddingCache`. Those models are not present in the current runtime and must not be recreated unless a concrete feature requires them.

## Relationships and ownership

```text
User 1 ─── * Conversation
User 1 ─── * Feedback
User 1 ─── * PasswordResetToken
Conversation 1 ─── 0..1 Feedback
```

Conversation and feedback queries are scoped to the authenticated user. This is a security boundary, not just a UI convention. A client-supplied user identifier must never be used to bypass the session-derived owner.

## Schema compatibility

Application startup creates missing tables and includes a lightweight compatibility step for older local SQLite databases, including the account fields introduced during authentication work. This approach supports the local portfolio demo. It is not a replacement for formal migrations in production.

Before changing a deployed schema:

1. Back up the database.
2. Test the change against a copy of the production schema.
3. Prefer Alembic or Flask-Migrate for repeatable migrations.
4. Deploy the application and schema change in a controlled order.
5. Verify authentication and ownership queries after migration.

## Database configuration

Local development:

```dotenv
DATABASE_URL=sqlite:///career_copilot.db
```

Production-oriented example:

```dotenv
DATABASE_URL=postgresql://username:password@host:5432/career_copilot
```

Credentials must be supplied through a secrets manager or deployment environment and must not be committed to Git.

## Verification

Run the database test and the full suite:

```bash
python test_db_setup.py
pytest -q
```

The tests verify table initialization, account creation, password hashing, reset-token behavior, conversation ownership, feedback ownership, and analytics isolation.

## Current limitations and next steps

The repository does not yet include Alembic, connection-pool tuning, a database backup scheduler, or an administrative data-retention workflow. These are appropriate next steps before production use, especially when moving from SQLite to PostgreSQL.

## Related documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [SETUP.md](SETUP.md)
- [README.md](README.md)
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

## License

MIT License. See [LICENSE.md](LICENSE.md).
