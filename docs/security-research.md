# Security and OAuth implementation notes

## Google OAuth 2.0
Source: https://developers.google.com/identity/protocols/oauth2/web-server

Google's server-side web flow uses the authorization-code pattern. The application configures `client_id`, an exact `redirect_uri`, `response_type=code`, a narrow `scope`, and a cryptographically random `state` value. The callback must verify `state` before exchanging the authorization code. The authorization code is then exchanged for tokens, and redirect URI mismatches and invalid grants must be handled. Career Copilot will request only OpenID identity scopes (`openid email profile`) and will not request Drive or Calendar access.

## Password reset
Source: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html

OWASP recommends consistent responses for existing and non-existing accounts to reduce account enumeration, sufficiently long cryptographically random tokens, secure storage of the token, single use, expiry after an appropriate period, no password change until a valid token is presented, a URL-based reset flow, confirmation of the new password, and no automatic login after reset. The implementation will hash the reset token in the database, expire it after 30 minutes, invalidate it after use, and send a generic response from the request endpoint.
