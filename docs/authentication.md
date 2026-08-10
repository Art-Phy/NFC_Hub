
## Authentication Architecture

### Scope

This document defines the authentication architecture for NFC Hub before authentication code is implemented. It is a planning and design reference, not a description of working software.

The initial strategy is:

- Conventional email-and-password authentication.
- Argon2id password hashing with `argon2-cffi`.
- Opaque server-side sessions persisted in the database.
- Random session tokens stored in browser cookies.
- Only cryptographic hashes of session tokens persisted.
- `HttpOnly`, `SameSite=Lax` session cookies.
- `Secure` cookies in production.
- Synchronizer CSRF tokens for state-changing server-rendered forms.
- Explicit FastAPI dependencies for page and API authentication.
- No JWT authentication.
- No authentication based on NFC tag UID or public NFC URLs.

The document distinguishes:

- Architectural decisions.
- Requirements for the next coding increment.
- Features intentionally postponed.

---

### 1. Authentication Method

NFC Hub uses conventional email-and-password authentication through server-rendered HTML forms.

The email address is the login identifier. The existing `User` model already provides:

- A normalized and uniquely indexed email address.
- A `password_hash` column.
- An active/inactive state.

No change to the existing user model is required solely to support authentication.

This approach fits the initial server-rendered Jinja2 frontend and small modular-monolith architecture. OAuth, social login and multi-factor authentication are outside the MVP scope.

---

### 2. Server-Side Session Strategy

NFC Hub uses opaque server-side sessions persisted in the database.

Each successful login or registration creates a new authenticated session associated with the authenticated user. Multiple concurrent sessions are allowed so a user can remain logged in on different browsers or devices.

The browser receives only a random, unguessable session token. The cookie contains no user data or signed payload. Session ownership, state and expiration remain on the server.

This provides:

- Immediate revocation by deleting a database row.
- Centralized session expiration.
- No application-wide signing secret for the session mechanism.
- No client influence over session identity or contents.

---

### 3. Session Persistence and Valid States

The next coding increment introduces a `sessions` table with these fields:

- `id` — internal integer primary key used for bookkeeping and operational logging.
- `user_id` — nullable foreign key to `users.id` with `ON DELETE CASCADE`.
- `token_hash` — unique, indexed SHA-256 hash of the raw session token.
- `csrf_token` — random server-side token used by the synchronizer-token CSRF pattern.
- `created_at` — timezone-aware UTC creation timestamp.
- `expires_at` — timezone-aware UTC expiration timestamp.

Exactly two session states are valid:

- **Anonymous pre-authentication session:** `user_id IS NULL`.
- **Authenticated session:** `user_id IS NOT NULL`.

The following invariants apply:

- Anonymous sessions exist only to support CSRF protection for login and registration.
- Anonymous sessions never authorize protected operations.
- Authentication dependencies reject sessions whose `user_id` is null.
- An authenticated session is always a newly inserted row.
- An anonymous row is never updated, promoted or bound to a user.
- Successful authentication deletes the anonymous row and inserts a new authenticated row atomically.
- No intermediate or partially authenticated state is valid.

The model, indexes and Alembic migration belong to the next coding increment.

---

### 4. Session Token Generation and Storage

Raw session tokens are generated with:

```python
secrets.token_urlsafe(32)
```

This provides 32 bytes of entropy encoded as a URL-safe string.

Rules:

- Generate a new independent token for every session.
- Never accept a session token chosen by the client.
- Never reuse a token.
- Never persist or log the raw token.
- Store the raw token only in the browser cookie.
- Persist only `sha256(raw_token).hexdigest()` in `token_hash`.

For each request, the application:

1. Reads the raw token from the cookie.
2. Computes its SHA-256 digest.
3. Queries the unique `token_hash` column.
4. Rejects missing, unknown or expired sessions.

A constant-time comparison is unnecessary for the indexed database lookup because no raw submitted secret is compared directly with a stored raw secret.

Direct comparison of a submitted CSRF token with its stored value must use `secrets.compare_digest()`.

---

### 5. Session Expiration, Revocation and Cleanup

Every session has an absolute `expires_at` determined by its type when created.

A session is invalid when the current time is at or after `expires_at`, regardless of recent activity. Sliding expiration is not included initially.

Revocation means deleting the session row. No `revoked_at` column or boolean revocation flag is introduced without a concrete auditing requirement.

- Logout deletes the current authenticated session.
- A future password-change workflow must delete every authenticated session belonging to the affected user.
- Expired anonymous and authenticated rows are eligible for cleanup.

Bounded opportunistic cleanup may run when creating a session. It must not perform an unbounded deletion on every request. For example, each cleanup operation may delete only a limited batch of expired rows.

Cleanup is maintenance work independent of authentication transitions:

- Cleanup failure must not invalidate an authentication transaction that has already committed.
- Cleanup must not prevent the response from setting the authenticated cookie.
- An inactive installation may retain expired rows until another session is created.

Scheduled or batch cleanup is postponed.

---

### 6. Session Lifetime Settings

Two centralized settings determine session lifetime:

- `authenticated_session_ttl_seconds = 2592000` — 30 days.
- `anonymous_session_ttl_seconds = 900` — 15 minutes.

The server-side `expires_at` value is authoritative. Cookie `Max-Age` and `Expires` reflect the corresponding session lifetime but do not replace server-side expiration checks.

---

### 7. Session Cookie Configuration

The default cookie name is `nfc_hub_session`.

Cookie attributes:

- `HttpOnly`
- `SameSite=Lax`
- `Path=/`
- No `Domain` attribute, making the cookie host-only.
- `Max-Age` matching the session type.
- `Expires` matching `Max-Age`.
- `Secure` according to the centralized setting described below.

Anonymous and authenticated sessions use the same cookie name but always use different raw token values.

The cookie value must never be:

- Reused for another purpose.
- Used as the CSRF token.
- Stored in the database.
- Logged.

---

### 8. Centralized Session and Cookie Settings

Cookie security behavior must be centralized rather than implemented through repeated environment comparisons in routes or dependencies.

| Environment variable | Setting | Initial default | Requirement |
| --- | --- | --- | --- |
| `NFC_HUB_SESSION_COOKIE_NAME` | `session_cookie_name` | `nfc_hub_session` | Used for both session types |
| `NFC_HUB_SESSION_COOKIE_SECURE` | `session_cookie_secure` | `False` in development | Must be `True` in production |
| `NFC_HUB_AUTHENTICATED_SESSION_TTL_SECONDS` | `authenticated_session_ttl_seconds` | `2592000` | 30 days |
| `NFC_HUB_ANONYMOUS_SESSION_TTL_SECONDS` | `anonymous_session_ttl_seconds` | `900` | 15 minutes |

Production must fail fast if secure cookies are not enabled.

Local development over plain HTTP may set `session_cookie_secure = False`, because browsers do not send `Secure` cookies over plain HTTP.

Cookie construction must consume the centralized settings and must not contain scattered checks such as `environment == "production"`.

---

### 9. Password Hashing

Package: `argon2-cffi`.

Algorithm: Argon2id.

Initial parameters:

```text
memory_cost=19456 KiB
time_cost=2
parallelism=1
```

These parameters are centralized in a dedicated password service.

`argon2-cffi` provides:

- `PasswordHasher.hash()`
- `PasswordHasher.verify()`
- `PasswordHasher.check_needs_rehash()`

The library generates a new random salt for every password hash. The application never generates or manages salts itself.

The resulting self-describing hash contains the algorithm version and parameters, allowing future changes without a database-schema migration.

The initial parameters must be benchmarked on the deployment hardware. They may be increased when sufficient performance margin exists. Any reduction below the selected security baseline must be treated as an explicit, measured deployment exception rather than an automatic response to slow hardware.

Parameters used to create new hashes remain controlled by the application. If protection against abnormally expensive legacy or manipulated hashes is required, validation must be implemented deliberately because verification parameters are encoded in each stored hash.

The dependency is added and documented in `pyproject.toml` during the next coding increment.

---

### 10. Password Verification and Hash Upgrades

Password verification uses the library's secure verification mechanism through `PasswordHasher.verify()`.

If the email is unknown or the account is inactive, verification still runs against a fixed valid dummy hash. This reduces observable timing differences between existing and unknown accounts without claiming that the complete login response has constant execution time.

After successful verification:

1. Call `check_needs_rehash()`.
2. If required, hash the submitted password with the current parameters.
3. Persist the replacement value in `password_hash`.

The existing `User.updated_at` timestamp should reflect the update.

This supports parameter changes and future algorithm migration through the self-describing hash format. Supporting several algorithms simultaneously is postponed.

---

### 11. Anonymous Pre-Authentication Sessions

Anonymous sessions provide CSRF protection before authentication exists.

When an unauthenticated visitor requests `GET /login` or `GET /register`:

1. Resolve any existing valid anonymous session.
2. Create one if none exists.
3. Store `user_id IS NULL`.
4. Generate a fresh session token and CSRF token.
5. Set `expires_at` from `anonymous_session_ttl_seconds`.
6. Set the anonymous session cookie.
7. Render the CSRF token as a hidden form value.

Rules:

- Anonymous sessions never authorize protected resources.
- Failed login or registration may retain the anonymous session so the form can be rendered again.
- Successful login or registration deletes the anonymous row.
- Its session token, CSRF token and row are never reused.
- The authenticated session receives a new session token, new CSRF token and new database row.

This prevents session fixation because an attacker-controlled anonymous token can never become authenticated.

If `GET /login` or `GET /register` receives a valid authenticated session, it must:

- Redirect to the authenticated management entry point.
- Preserve the authenticated cookie.
- Not create an anonymous session.

---

### 12. Login Lifecycle

Routes:

- `GET /login` renders the CSRF-protected login form.
- `POST /login` verifies the form and establishes an authenticated session.

A successful login follows this order:

1. Resolve and validate the anonymous session.
2. Validate the submitted CSRF token.
3. Normalize the email address.
4. Verify the credentials or run dummy-hash verification.
5. Generate a fresh authenticated session token.
6. Generate a fresh authenticated CSRF token.
7. Atomically:
   - Delete the anonymous session row.
   - Insert the authenticated session row with non-null `user_id`.
   - Set `expires_at` from `authenticated_session_ttl_seconds`.
   - Commit both persistence changes as one transaction.
8. Roll back the complete transaction if the authenticated session cannot be created.
9. Replace the browser cookie only after the transaction commits.
10. Redirect with `303 See Other` only after setting the cookie.
11. Optionally run bounded cleanup independently of the completed authentication transition.

A failed login:

- Returns the generic message `Invalid credentials`.
- Does not reveal whether the email exists, the password is wrong or the account is inactive.
- Creates no authenticated session or authenticated cookie.
- May retain the anonymous session to re-render the form.
- Logs the outcome without sensitive values.

The anonymous row and token are never promoted or reused.

---

### 13. Registration Lifecycle

Routes:

- `GET /register` renders the CSRF-protected registration form.
- `POST /register` validates the form, creates the user and establishes an authenticated session.

A successful registration follows this order:

1. Resolve and validate the anonymous session.
2. Validate the submitted CSRF token.
3. Normalize the email address.
4. Validate uniqueness.
5. Validate the password according to rules already defined elsewhere.
6. Hash the password with Argon2id.
7. Generate a fresh authenticated session token.
8. Generate a fresh authenticated CSRF token.
9. Atomically:
   - Insert the new user.
   - Delete the anonymous session row.
   - Insert the authenticated session row with non-null `user_id`.
   - Set `expires_at` from `authenticated_session_ttl_seconds`.
   - Commit all persistence changes as one transaction.
10. Roll back the complete transaction if any persistence operation fails.
11. Replace the browser cookie only after the transaction commits.
12. Redirect with `303 See Other` only after setting the cookie.
13. Optionally run bounded cleanup independently of the completed registration transition.

Duplicate-email handling must remain generic enough to avoid unnecessary account enumeration. The response may direct the visitor to login without confirming whether an account exists.

A failed registration creates:

- No committed user when the transaction fails.
- No authenticated session.
- No authenticated cookie.

This document does not introduce a broader password policy.

---

### 14. Logout Lifecycle

Logout must:

1. Accept only `POST`.
2. Require a valid authenticated session.
3. Require a valid CSRF token.
4. Delete only the current authenticated session row.
5. Clear the session cookie.
6. Redirect to a public page with `303 See Other`.

Clearing the cookie must use:

- The same cookie name.
- The same `Path`.
- The same `Domain` behavior. NFC Hub does not set `Domain`, so the deletion cookie remains host-only.
- `Max-Age=0`.
- An expiration date in the past.

`Secure`, `HttpOnly` and `SameSite` should remain consistent when constructing the deletion header, although cookie identity is determined by name, path and domain.

Logout must not create an anonymous replacement session. A later request to `GET /login` or `GET /register` may create one when required.

After the row is deleted, a copied cookie token no longer resolves to a valid session.

---

### 15. CSRF Protection

NFC Hub uses the synchronizer-token pattern for server-rendered forms.

Every state-changing form must include the current session's CSRF token in a hidden field.

The CSRF token:

- Is generated with `secrets.token_urlsafe(32)`.
- Is stored server-side in the session row.
- Is regenerated for every new session.
- Is never stored in the session cookie.
- Is never logged.

On submission:

1. Resolve the session once.
2. Read the submitted CSRF value.
3. Compare it with the stored token using `secrets.compare_digest()`.
4. Reject missing sessions, missing tokens and mismatches with a generic error.

The same mechanism protects:

- Login.
- Registration.
- Logout.
- Future state-changing management forms.

`SameSite=Lax` complements but does not replace CSRF-token validation.

The synchronizer-token pattern is preferred because NFC Hub already maintains server-side session state and can bind each CSRF token directly to its session.

---

### 16. FastAPI Authentication Dependencies

The authentication module must separate session resolution from presentation-specific failure behavior.

Proposed responsibilities:

- `get_current_session`
  - Reads the raw cookie.
  - Hashes it with SHA-256.
  - Resolves the session by `token_hash`.
  - Rejects expired sessions.
  - Resolves the session only once per request so authentication and CSRF validation can share it.

- `resolve_current_user`
  - Uses the resolved session.
  - Requires non-null `user_id`.
  - Resolves the corresponding user.
  - Rejects inactive users.
  - Returns the authenticated user or an internal absent/invalid result.
  - Does not redirect or construct an HTTP response.

- `require_page_user`
  - Wraps the core resolver for server-rendered pages.
  - Redirects unauthenticated requests to `/login`.

- `require_api_user`
  - Wraps the core resolver for API endpoints.
  - Returns `401 Unauthorized` when authentication is absent or invalid.

- `require_csrf`
  - Validates the hidden form value against the resolved session's CSRF token.

- `get_anonymous_session`
  - Resolves or creates the anonymous session required by login and registration forms.
  - Never replaces a valid authenticated session.

The final names may follow existing project conventions, but page and API failure behavior must remain explicit and independently testable.

---

### 17. Application Secrets

The selected authentication design does not require an application-wide signing secret:

- Session tokens are random and only their hashes are persisted.
- Password hashes contain Argon2-generated salts.
- CSRF tokens are random and stored server-side.

If a future feature requires signed or encrypted values, such as password-recovery tokens:

- Add a dedicated centralized setting loaded from an environment variable.
- Do not provide a production default.
- Fail fast in production if the value is missing or invalid.
- Never commit or log the value.
- Do not create or commit `.env` files containing secrets.

---

### 18. Authorization for Future NFC Tag Operations

Every tag-management operation must derive the current user from the authenticated session.

Rules:

- The service receives the authenticated user from the authentication dependency.
- Queries are scoped by both the tag identifier and `user_id`.
- The client never supplies the authoritative owner identifier.
- A tag owned by another user is treated as not found with `404 Not Found`, avoiding disclosure of its existence.

The public route `GET /t/{token}`:

- Does not authenticate the visitor.
- Does not grant management access.
- Resolves only public behavior.
- Does not treat the public token or NFC contents as proof of identity.

---

### 19. Logging and Sensitive-Data Protection

User-facing errors must be generic and must not expose stack traces or internal details.

Never log:

- Passwords.
- Password hashes.
- Raw session tokens.
- Session-token hashes.
- CSRF tokens.

Operational logs may include:

- The internal session-row `id`.
- The user `id` when known.
- Client IP address.
- Login or registration outcome.

Storage rules:

- Passwords and raw session tokens are never persisted.
- Password hashes and session-token hashes are persisted as required but never logged.
- CSRF tokens are persisted server-side as required by the synchronizer-token design but never logged or placed in the session cookie.
- Sensitive values are persisted only when explicitly required by the architecture.

Production runs with debug mode disabled.

---

### 20. Testing Strategy

Tests must follow the existing repository conventions:

- Isolated in-memory or temporary databases.
- Settings-cache clearing through the existing `conftest.py` fixture.
- FastAPI `TestClient` with cookie handling.
- No external services.
- No creation or modification of `nfc_hub.db`.

Required coverage:

#### Password hashing

- Different salts produce different hashes for the same password.
- Correct passwords verify successfully.
- Incorrect passwords fail.
- Stale parameters trigger rehash detection.
- Unknown or inactive users execute dummy-hash verification.

#### Session tokens and states

- Tokens have sufficient entropy and URL-safe format.
- Only token hashes are persisted.
- Anonymous sessions always have `user_id IS NULL`.
- Authenticated sessions always have non-null `user_id`.
- No intermediate state is produced.
- Anonymous sessions cannot authorize protected resources.
- Missing, unknown and expired sessions are rejected.

#### Cookies

- Correct name, `HttpOnly`, `SameSite`, `Path`, `Secure`, `Max-Age` and `Expires`.
- Anonymous and authenticated lifetimes differ.
- Production rejects insecure cookie configuration.
- Cookie deletion uses matching name, path and domain behavior.

#### CSRF

- Missing session.
- Missing token.
- Incorrect or tampered token.
- Valid constant-time comparison.
- Coverage for login, registration and logout.

#### Login

- Success deletes the anonymous row and inserts a fresh authenticated row atomically.
- The authenticated token and CSRF token differ from the anonymous values.
- Transaction failure preserves the anonymous session and creates no authenticated session.
- The cookie changes only after commit.
- Wrong password, unknown email and inactive account receive generic failures.
- Successful POST redirects with `303 See Other`.

#### Registration

- Success creates the user and authenticated session while deleting the anonymous row atomically.
- Duplicate email receives a generic response.
- Transaction failure commits neither user nor authenticated session.
- The cookie changes only after commit.
- Successful POST redirects with `303 See Other`.

#### Authenticated visitors

- `GET /login` and `GET /register` redirect authenticated users.
- Their authenticated cookie is not overwritten.
- No anonymous session is created.

#### Dependencies

- Page dependencies redirect unauthenticated requests.
- API dependencies return `401 Unauthorized`.
- Anonymous, expired and inactive-user sessions are rejected.

#### Logout

- Only `POST` is accepted.
- Authentication and CSRF are required.
- Only the current session is deleted.
- The cookie is cleared correctly.
- No anonymous session is created in the logout response.
- The redirect uses `303 See Other`.

Future tag-ownership tests belong to the tag-management increment.

All existing tests must continue to pass.

---

### 21. Rejected Alternatives

1. **JWT authentication**

   Rejected because it offers no useful advantage for the initial server-rendered monolith, complicates immediate revocation and introduces key management and claim-validation requirements. JWT can use symmetric or asymmetric cryptography; the rejection does not depend on assuming a shared secret.

2. **Client-side signed session cookies**

   Rejected because server-side sessions provide simpler revocation, smaller client state and no session-signing key requirement.

3. **In-memory or Redis-backed sessions**

   Rejected for the initial implementation because they introduce additional infrastructure and operational complexity. Redis can provide persistence when configured, but it is unnecessary for the current deployment architecture.

4. **bcrypt or PBKDF2**

   Rejected in favor of Argon2id and its memory-hard design.

5. **Double-submit CSRF**

   Rejected because the application already maintains server-side session state. A synchronizer token binds CSRF protection directly to the corresponding session and fits the existing architecture more naturally.

6. **Authentication by NFC UID or NFC contents**

   Rejected because identifiers and URLs can be copied and do not prove identity.

7. **Treating public NFC URLs as secrets**

   Rejected because possession of a public URL must never grant management access.

8. **OAuth, social login, email verification, password recovery, MFA and role-based authorization**

   Postponed beyond the MVP.

9. **Sliding session expiration**

   Rejected initially in favor of predictable absolute expiration.

10. **SPA or client-side authentication**

    Rejected because the initial frontend uses server-rendered HTML forms.

---

### 22. Next Coding Increment

The next coding increment includes only:

- Centralized authentication, session and cookie settings.
- `argon2-cffi` dependency and password service.
- User registration.
- Session persistence model.
- Alembic migration for the `sessions` table.
- Anonymous pre-authentication sessions.
- Login and logout workflows.
- CSRF protection for those workflows.
- Page-oriented and API-oriented authentication dependencies.
- Automated tests for the implemented behavior.

It does not include:

- NFC tag persistence or ownership implementation.
- Password reset or account-management pages.
- Rate limiting.
- MFA or OAuth.
- Sliding session expiration.
- Scheduled cleanup jobs.
- Unrelated frontend work.

---

### 23. Deferred Features

- Login rate limiting.
- Sliding session renewal.
- Per-session client metadata.
- Scheduled or batch session cleanup.
- Password reset and recovery.
- Email verification.
- Account-management pages.
- Password changes with global session revocation.
- Additional password algorithms.
- Additional security headers.
- Abuse detection for public NFC routes.

The exact authenticated management redirect target is a route-level implementation detail and does not alter this architecture.
