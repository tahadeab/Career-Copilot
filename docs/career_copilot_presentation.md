# Career Copilot — Project Presentation

## Cover
Career Copilot
Secure, Explainable Career Guidance for Students
Taha Deab · Portfolio Project · 2026

## Slide 1
### The product turns career questions into measurable next steps
- Bilingual guidance for students and early-career builders
- Private accounts keep conversations and feedback isolated
- Explainable responses expose intent, confidence, and sentiment
- Designed as a portfolio-ready product, not a single chatbot demo

## Slide 2
### A focused workflow connects guidance to outcomes
- Ask: the user describes a learning, CV, interview, AI, or project challenge
- Understand: the service detects language, classifies intent, and estimates confidence
- Guide: the assistant returns a structured, actionable response
- Improve: feedback and personal analytics reveal what is useful over time

## Slide 3
### The architecture keeps product boundaries clear
- Responsive browser UI with English-first copy and Arabic RTL support
- Flask REST API with protected session-based routes
- Service layer separates language detection and explainable response policy
- SQLAlchemy models persist users, reset tokens, conversations, feedback, and training data
- SQLite works locally; `DATABASE_URL` supports a production database configuration

## Slide 4
### Authentication makes the chatbot a private workspace
- Local registration stores only one-way password hashes
- HttpOnly, SameSite sessions define the authenticated user on the server
- Chat, history, feedback, and analytics derive ownership from the session
- Password recovery uses random, hashed, single-use tokens with a 30-minute expiry
- The reset endpoint returns a generic response to reduce account enumeration risk

## Slide 5
### Google OAuth adds a trusted identity path without storing access tokens
- Uses Google's server-side authorization-code flow
- Requests only `openid email profile`
- Validates the OAuth `state` value before exchanging the code
- Links a verified Google identity to an existing email or creates a new account
- Production configuration requires HTTPS, exact redirect URIs, and managed secrets

## Slide 6
### Personal analytics turns conversations into product insight
- Period selector: 7, 30, or 90 days
- KPI cards: messages, active days, average confidence, and top intent
- Intent and language breakdowns expose the user's guidance pattern
- Daily and hourly activity show engagement rhythm
- Feedback totals and satisfaction rate create a measurable improvement loop

## Slide 7
### The implementation demonstrates production-minded engineering
- 10 integration tests cover authentication, isolation, recovery, analytics, and validation
- API-first design supports future mobile clients or a hosted LLM/RAG layer
- Development defaults remain offline-friendly and transparent
- Next hardening steps: CSRF protection, rate limiting, HTTPS, observability, and formal migrations

## Slide 8
### A strong CV story connects technology to impact
**Suggested CV entry**

Career Copilot — Secure Explainable Career Guidance Platform

Built and tested a Flask-based bilingual career assistant with SQLAlchemy user isolation, secure password hashing and single-use email recovery tokens, optional Google OAuth 2.0, explainable intent and confidence signals, user-scoped analytics dashboards, feedback-based satisfaction metrics, responsive RTL-aware UI, REST APIs, and automated integration tests.

**Technology keywords:** Python · Flask · SQLAlchemy · SQLite/PostgreSQL · OAuth 2.0 · SMTP · REST APIs · Pytest · Responsive UI

## Slide 9
### References and implementation notes
- Google for Developers: Using OAuth 2.0 for Web Server Applications
- OWASP Cheat Sheet Series: Forgot Password
- Repository: `github.com/tahadeab/Career-Copilot`
- Demonstrated verification: 10 automated tests passed; Python syntax validation passed
