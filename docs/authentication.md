# Authentication Architecture

## Scope

This document defines the authentication architecture for NFC Hub before any
authentication code is implemented. It is a planning and design document and
does not describe working software.

The document separates:

- Decisions for the initial implementation.
- Requirements for the next coding increment.
- Features intentionally postponed until later.

The authentication strategy is:

- Conventional email-and-password authentication.
- Argon2id password hashing using `argon2-cffi`.
- Opaque server-side sessions.
- Only a random session token stored in the browser cookie.
- Only a cryptographic hash of that token stored in the database.
- `HttpOnly` session cookie with `SameSite=Lax`.
- `Secure` enabled in production.
- CSRF tokens for all state-changing server-rendered forms.
- FastAPI dependencies for resolving the current user and requiring
  authentication.
- No JWT authentication.
- No authentication based on NFC tag UID.
- No assumption that public NFC URLs are secret.

---

## 1. Authentication Method

Decision: conventional email-and-password authentication through server-rendered
HTML forms.

Why:

- The first frontend is server-rendered with Jinja2. Form-based authentication
  is the natural fit.
- The domain is a small modular monolith. A simple email-and-password model
  keeps the attack surface, code and maintenance burden small.
- Social login, OAuth and multi-factor authentication are not required by the
  MVP scope defined in `PROJECT.md`.

The email address is the login identifier. The existing `User` model already
stores a normalized, uniquely indexed email address and a `password_hash`
column. No change to that model is needed to support authentication.

---

## 2. Server-Side Session Strategy

Decision: opaque server-side sessions persisted in the database.

Each successful login or registration creates a new authenticated session tied
to the authenticated user. A user may hold multiple concurrent authenticated
sessions, one per logged-in device or browser.

The browser receives only a random, unguessable session token that is opaque to
the client. The session identity, lifetime and owner live on the server. The
browser cookie carries no user data and no cryptography to interpret.

Why:

- Sessions must be revocable. Deleting a database row is immediate and
  deterministic.
- Session data can change without invalidating cookies or requiring signed
  payloads.
- No shared signing secret is needed, because the token is random and is never
  interpreted by the server as data.

The client must never be able to select, guess or influence the session
identity.

---

## 3. Session Persistence and Valid Session States

A future `sessions` table will be introduced in the next coding increment. Its
shape is defined here so the implementation is designed once.

Fields:

- `id` — internal integer primary key, used only for bookkeeping and logging.
- `user_id` — foreign key to `users.id`, nullable, with `ON DELETE CASCADE`.
- `token_hash` — unique, indexed column holding the SHA-256 hash of the session
  token. Only this hash is ever stored.
- `csrf_token` — random value generated with a cryptographically secure PRNG,
  bound to this session, used by the synchronizer CSRF pattern. It is stored
  server-side and must never be placed in the session cookie.
- `created_at` — timezone-aware UTC creation timestamp.
- `expires_at` — timezone-aware UTC expiration timestamp.

The `user_id` column is nullable, but exactly two session states are valid:

- **Anonymous pre-authentication session:** `user_id IS NULL`.
- **Authenticated session:** `user_id IS NOT NULL`.

Invariants:

- Anonymous sessions exist only to host the CSRF token on registration and
  login forms.
- Anonymous sessions can never authorize access to protected resources.
- Authentication dependencies reject every session whose `user_id` is null.
- An authenticated session is always a newly created row. It is never created by
  updating, promoting, reusing or binding an anonymous row.
- A successful login or registration always ends with the anonymous row deleted
  and a new authenticated row created (sections 13 and 14).
- No intermediate or partially authenticated state is valid.
- These invariants must be covered by automated tests (section 21).

A future Alembic migration must create this table and its indexes. Creating the
model and its migration belongs to the next coding increment.

---

## 4. Session Token Generation and Server-Side Storage

Generation:

- The raw session token is generated with `secrets.token_urlsafe(32)`.
- This produces 32 bytes of entropy (256 bits) encoded as a URL-safe string,
  long enough to be difficult to guess.
- A new independent token is generated for every new session. Tokens are never
  reused.
- The raw token only ever lives in memory at creation time and in the browser
  cookie.

Storage:

- Only `sha256(raw_token).hexdigest()` is persisted, in the `token_hash`
  column. The raw token is never stored.

Lookup and comparison:

- On every request the application reads the raw token from the cookie,
  computes its SHA-256 hex digest, and queries the unique `token_hash` column
  directly.
- The raw token is never compared with a stored secret, so a constant-time
  comparison is not required for the database lookup itself.
- Constant-time comparison with `secrets.compare_digest()` is required whenever
  a submitted value is directly compared with a stored secret, specifically for
  CSRF-token verification (section 16).

---

## 5. Session Expiration, Revocation and Cleanup

Expiration:

- Every session has an absolute `expires_at` calculated from its type at
  creation time.
- A session is rejected as soon as the current time is at or past
  `expires_at`, regardless of recent activity. Sliding renewal is not
  implemented in the initial increment.

Revocation:

- Revocation means deleting the corresponding session row. No `revoked_at`
  column and no boolean revocation field are added unless a concrete auditing
  requirement appears.
- Logout deletes only the current authenticated session (section 15).
- A future password-change implementation must delete all sessions belonging to
  the affected user.

Cleanup:

- Expired rows of either session type are eligible for cleanup.
- Opportunistic cleanup may run when a new session is created. The
  implementation must avoid an unbounded delete on every request, for example
  by deleting only a bounded batch of expired rows.
- Opportunistic cleanup is not complete session lifecycle management. An
  inactive installation may retain expired rows until the next session creation.
  This is a known property of the initial implementation.
- Scheduled or batch cleanup is postponed to a later increment.

---

## 6. Session Lifetime Settings

Two centralized settings control session expiration. The cookie `Max-Age`
reflects the lifetime of the current session; the expiration itself is a
server-side session concern, not a cookie concern.

Initial architectural defaults:

- Authenticated session: `authenticated_session_ttl_seconds = 2592000` (30
  days).
- Anonymous pre-authentication session: `anonymous_session_ttl_seconds = 900`
  (15 minutes).

Both values are centralized settings and may be configured later.

---

## 7. Session Cookie Name and Security Attributes

Cookie name: `nfc_hub_session`, configured through `session_cookie_name`
(`NFC_HUB_SESSION_COOKIE_NAME`).

Security attributes:

- `HttpOnly` — the cookie cannot be read by JavaScript.
- `SameSite=Lax` — the cookie is not sent on cross-site POST requests,
  complementing the CSRF token check.
- `Path=/` — the cookie applies to the whole application.
- No `Domain` attribute — the cookie is host-only.
- `Max-Age` set to the lifetime of the session being established, with a
  matching `Expires`.
- `Secure` — behavior defined in section 8.

The same cookie name and construction are used for anonymous and authenticated
sessions.

The cookie value is the raw session token. It must not be:

- Reused for any other purpose.
- Used as the CSRF token.
- Stored in the database.
- Logged.

---

## 8. The Secure Attribute in Development and Production

Decision: cookie security behavior must be centralized into application
settings, not expressed as ad-hoc string comparisons scattered across route or
middleware code.

Requirements:

- A dedicated centralized setting, `session_cookie_secure`
  (`NFC_HUB_SESSION_COOKIE_SECURE`), controls whether session cookies carry
  `Secure`.
- Production requires `session_cookie_secure = True`. In a production
  environment the application must fail fast if secure cookies cannot be
  honored, rather than silently weakening the attribute.
- Local development over plain HTTP may use `session_cookie_secure = False`,
  because the `Secure` attribute would prevent cookies from being sent.
- The implementation may derive the default from the configured environment,
  but cookie construction must consume the dedicated centralized setting, not
  repeated `environment == "production"` comparisons.

Settings summary:

| Environment variable | Centralized setting | Default | Notes |
| --- | --- | --- | --- |
| `NFC_HUB_SESSION_COOKIE_NAME` | `session_cookie_name` | `nfc_hub_session` | Cookie name for both session types |
| `NFC_HUB_SESSION_COOKIE_SECURE` | `session_cookie_secure` | `False` in development | Required `True` in production |
| `NFC_HUB_AUTHENTICATED_SESSION_TTL_SECONDS` | `authenticated_session_ttl_seconds` | `2592000` | 30 days |
| `NFC_HUB_ANONYMOUS_SESSION_TTL_SECONDS` | `anonymous_session_ttl_seconds` | `900` | 15 minutes |

---

## 9. Password Hashing Library and Algorithm

Package: `argon2-cffi`.

Algorithm: Argon2id.

Why Argon2id:

- It is the OWASP recommended password hashing algorithm.
- It is memory-hard, which raises the cost of brute-force attacks with parallel
  hardware.
- The reference implementation is well maintained.

Why `argon2-cffi` directly:

- It produces a self-describing hash string that embeds the algorithm, version
  and parameters.
- It provides `PasswordHasher.hash()`, `PasswordHasher.verify()` and
  `PasswordHasher.check_needs_rehash()`, covering the full hashing lifecycle.
- A small dedicated password service isolates the library. A wrapper such as
  `pwdlib` is unnecessary for the single algorithm used here.

The library generates a random salt for every hash. The application never
manages salts.

The dependency must be added in the next coding increment and justified in
`pyproject.toml`.

---

## 10. Recommended Argon2id Parameter-Management Strategy

Initial baseline (OWASP minimum recommendation for Argon2id):

- `memory_cost = 19456 KiB` (19 MiB).
- `time_cost = 2`.
- `parallelism = 1`.

These are the starting point for the initial implementation, not a fixed
production target.

Management rules:

- The parameters are declared once as a documented constant in the password
  service, not scattered over registration, login and verification code.
- The parameters are embedded in every self-describing hash string.
- The parameters must be benchmarked on the actual deployment hardware before
  production use. They may be increased over the baseline without changing the
  architecture, the session strategy, the database schema or the rest of the
  design.
- Because the column stores only the composed hash string, parameter changes do
  not require a schema migration.
- Each password gets a fresh random salt, so identical passwords produce
  different hashes.
- A reasonable upper bound for memory and time must be enforced when hashing or
  verifying to avoid excessive resource use on the server.

---

## 11. Password Verification and Future Hash Upgrades

Verification:

- Password verification is implemented by the library's secure verification
  mechanism (`PasswordHasher.verify()`).
- If the email is not found or the user is inactive, the application still runs
  verification against a fixed dummy hash so that observable differences
  between existing and unknown accounts are reduced. This is a defense against
  user enumeration through response differences; it does not claim constant
  execution time for the complete login response.

Future hash upgrades:

- After a successful verification, `check_needs_rehash()` detects that the
  stored hash does not match the currently configured parameters.
- If the hash is stale, the password is rehashed with the current parameters
  and the new value is stored in the existing `password_hash` column, which
  causes the `User.updated_at` timestamp to update. No schema change and no new
  model field are needed.
- This covers both parameter increases (section 10) and a future algorithm
  change expressed through the hash's algorithm prefix.
- Explicit migration between multiple supported algorithms is postponed;
  recognizing stale hashes is required behavior from the start.

---

## 12. Anonymous Pre-Authentication Sessions

Anonymous sessions exist only to provide CSRF protection on the registration
and login forms, which are submitted before any authenticated session exists.

Lifecycle:

1. `GET /login` or `GET /register` obtains or creates an anonymous session when
   no valid session cookie exists.
2. The anonymous row has `user_id IS NULL`, a fresh `csrf_token`, and
   `expires_at` derived from `anonymous_session_ttl_seconds`.
3. The session cookie is set with the anonymous token, so the form can be
   rendered with the CSRF token as a hidden value.
4. The anonymous session is destroyed when the user authenticates or registers
   (sections 13 and 14).

Rules:

- An anonymous session can never authorize access to protected resources
  (section 3).
- The anonymous token, CSRF token and database row never survive privilege
  elevation.
- On a failed login or registration the anonymous row may be kept so the form
  can re-render, but it must never become authenticated.

This design protects against session fixation: an attacker-supplied token can
never become an authenticated session, because authentication never promotes
the anonymous row and always issues fresh tokens.

Already-authenticated visitors:

- `GET /login` and `GET /register` redirect an already-authenticated user to the
  authenticated management entry point.
- They must not create an anonymous session and must not overwrite a valid
  authenticated cookie.
- Anonymous sessions are created only when no valid authenticated session exists
  and a pre-authentication form requires CSRF protection.

---

## 13. Login Lifecycle

Routes:

- `GET /login` — renders the login form. It obtains or creates an anonymous
  session (unless the visitor is already authenticated; see section 12) and
  exposes its CSRF token as a hidden form value.
- `POST /login` — validates the form, verifies credentials, and establishes an
  independent authenticated session.

Successful login:

1. Resolve the anonymous pre-authentication session.
2. Validate its CSRF token (section 16).
3. Verify the credentials (section 11). Timing-equalizing verification runs
   against a dummy hash when the email is unknown or the user is inactive.
4. Generate a new independent authenticated session token and a new independent
   CSRF token.
5. Perform the database transition atomically: delete the anonymous session row
   and create the new authenticated session row (non-null `user_id`, `expires_at`
   from `authenticated_session_ttl_seconds`) as one transaction. If creation
   fails, the transaction rolls back and the anonymous session is not partially
   removed.
6. Replace the browser cookie with the new authenticated session token and the
   attributes from sections 7 and 8, only after the transaction has committed.
7. Run bounded opportunistic cleanup of expired rows.
8. Redirect to the authenticated management interface, only after the cookie has
   been set.

Failed login:

- A generic failure message ("Invalid credentials") is shown regardless of
  whether the email does not exist, the password does not match, or the account
  is inactive. No response reveals whether the email is registered.
- No authenticated session is created. The anonymous session may be retained so
  the form can re-render.
- Login attempts are logged without sensitive values (section 20).

---

## 14. Registration Lifecycle

Routes:

- `GET /register` — renders the registration form. It obtains or creates an
  anonymous session (unless the visitor is already authenticated; see section
  12) and exposes its CSRF token as a hidden form value.
- `POST /register` — validates the form, creates the user, and establishes an
  independent authenticated session.

Successful registration:

1. Resolve the anonymous pre-authentication session.
2. Validate its CSRF token.
3. Normalize the email address and enforce uniqueness. Duplicate submissions
   must be handled generically (below).
4. Validate the password according to the currently defined rules and hash it
   with Argon2id using the parameters from section 10.
5. Generate a new independent authenticated session token and a new independent
   CSRF token.
6. Perform the database transition atomically: create the new `User`, delete the
   anonymous session row, and create the new authenticated session row
   (non-null `user_id`, `expires_at` from
   `authenticated_session_ttl_seconds`) as one transaction. Any failure rolls
   back the complete transition; the anonymous session is not partially removed.
7. Replace the browser cookie with the new authenticated session token, only
   after the transaction has committed.
8. Run opportunistic cleanup of expired rows.
9. Redirect only after the cookie has been set.

Duplicate-email handling:

- The response on a duplicate email must remain generic enough to avoid
  unnecessary account enumeration. The user is directed to the login workflow
  without asserting whether the account already exists.

Failure:

- A failed registration creates no authenticated session and no authenticated
  session cookie.

No broader password policy is defined by this document. Only the constraints
already defined elsewhere in the repository apply, and any further minimum
requirements are decided during implementation.

---

## 15. Logout Lifecycle

Logout must:

- Accept only `POST`.
- Require a valid authenticated session.
- Require a valid CSRF token.
- Delete only the current authenticated session row.
- Clear the cookie using:

  - The same cookie name.
  - The same `Path`.
  - The same `Domain` behavior. This design sets no `Domain`, so the cookie
    remains host-only.
  - `Max-Age=0`.
  - An expiration date in the past.

  `Secure`, `HttpOnly` and `SameSite` may be kept consistent when generating the
  deletion header, but cookie identity for removal is determined primarily by
  name, path and domain.
- Not create a replacement anonymous session during the logout response.
- Redirect to a public page after completion.

A later `GET /login` or `GET /register` may create a new anonymous session when
needed.

Because the authenticated row is deleted, a copied cookie value has no effect
after logout.

Future: a password change must delete all sessions belonging to the affected
user.

---

## 16. CSRF Protection for Server-Rendered Forms

Mechanism: synchronizer token pattern.

- Every state-changing server-rendered form carries a hidden field with the
  current session's CSRF token.
- The CSRF token is generated with `secrets.token_urlsafe(32)`, stored
  server-side as part of the session row, and regenerated whenever a new session
  is created.
- The token is never placed in the session cookie. It reaches the browser only
  as a hidden form value.
- On submission the submitted value is compared with the stored `csrf_token`
  using `secrets.compare_digest()` (constant-time). A missing token, missing
  session, or mismatch returns a generic error.
- The same mechanism covers the login and registration forms through the
  anonymous pre-authentication session, so a single CSRF mechanism is used
  across the whole application.
- `SameSite=Lax` complements the token check; both together protect
  state-changing requests.
- The CSRF check applies to every state-changing form, including logout and all
  future tag-management forms.

---

## 17. Authentication and Authorization Dependencies for FastAPI

Dependencies provided by the authentication module:

- `get_current_session` — resolves the raw cookie value, hashes it with
  SHA-256, queries the `token_hash` column, and returns the session row if it is
  valid and not expired. It resolves the session once per request so that
  authentication and CSRF checks share it. A session with `user_id IS NULL` is
  not an authenticated session.
- `resolve_current_user` — the core resolver. It depends on
  `get_current_session`, requires an authenticated session with non-null
  `user_id`, resolves the `User`, and rejects inactive users. It returns the
  authenticated user or indicates that authentication is absent or invalid; it
  never performs redirects and never returns HTTP responses.
- `require_page_user` — the server-rendered-page dependency. It wraps
  `resolve_current_user` and redirects (302) unauthenticated requests to
  `/login`.
- `require_api_user` — the API-oriented dependency. It wraps
  `resolve_current_user` and returns `401 Unauthorized` for unauthenticated
  requests.
- `require_csrf` — a dependency for all state-changing `POST` forms that
  verifies the hidden field against the session's `csrf_token` with
  `secrets.compare_digest()`.
- `get_anonymous_session` — used by the login and registration pages to obtain
  or create the anonymous pre-authentication session.

`resolve_current_user` is the single source of truth for "who is the current
user". `require_page_user` and `require_api_user` differ only in how they
present an authentication failure and must never duplicate the resolution
logic.

All dependencies consume the centralized session and cookie settings (sections
5, 6, 7 and 8); they do not compare `environment == "production"` inline.

---

## 18. Application Secret Configuration

The chosen design does not require a shared application secret:

- Session tokens are random and only their hashes are stored.
- Password hashes use Argon2 salts.
- CSRF tokens are random and stored server-side.

There is therefore no server key to protect, rotate or leak. No secret is
generated, committed, or required by this design.

Rule for future features that need a signed or encrypted value (for example,
email-based password-recovery tokens):

- Add a dedicated centralized setting loaded from an environment variable (for
  example `NFC_HUB_CRYPTO_KEY`).
- The value comes from the environment, never from a default, and a missing or
  weak value must fail fast at startup in a production environment.
- Never commit secrets, create `.env` files, or log the value.

---

## 19. Ownership Verification for Future NFC Tag Operations

Model:

- Every tag-management operation resolves the current user through
  `require_page_user` (or `resolve_current_user`) (section 17).
- The future tag service requires both the tag identifier and the current user,
  and scopes every query by `user_id`.
- The service never accepts an owner identifier from the client; the owner is
  derived exclusively from the authenticated session.

Behavior:

- A tag that exists but is not owned by the current user is treated as not
  found (HTTP 404), not as forbidden (HTTP 403), to avoid revealing which tags
  exist.
- The public resolution route `GET /t/{token}` must never authenticate the
  visitor. It resolves only the public behavior, never management capabilities,
  and never uses session state.

---

## 20. Error Handling, Logging and Sensitive-Data Protection

- User-facing errors are generic and never include stack traces or internal
  details.
- The following values must never be logged:

  - Passwords.
  - Password hashes.
  - Raw session tokens.
  - Session-token hashes.
  - CSRF tokens.

- Log instead operational identifiers only:

  - The session row `id` (the internal primary key), never the token or its
    hash.
  - The user id when known.
  - Client IP and outcome for login and registration attempts.

- `debug` remains disabled in production.
- Sensitive values are stored only when the selected architecture explicitly
  requires them:

  - Passwords and raw session tokens are never persisted.
  - Password hashes and session-token hashes are persisted as required by the
    design but are never logged.
  - CSRF tokens are persisted server-side as required by the synchronizer-token
    pattern but are never logged and never placed in the session cookie.

---

## 21. Testing Strategy

The next coding increment must add automated tests that follow the existing
repository conventions:

- Isolated in-memory or temporary databases.
- Settings-cache cleaning through the existing `conftest.py` fixture.
- FastAPI `TestClient` with cookie handling.

Required coverage:

- Hashing: unique salt per hash, verification success and failure, rehash
  detection.
- Session tokens: sufficient length, URL-safe format, only the hash stored.
- Session states: anonymous rows always have `user_id IS NULL`, authenticated
  rows always have non-null `user_id`, and no intermediate state is produced.
- Anonymous sessions: short lifetime (`anonymous_session_ttl_seconds`), cannot
  authorize protected resources.
- Cookie attributes: `HttpOnly`, `SameSite`, `Path`, `Secure` behavior per
  settings, `Max-Age` reflecting the session type.
- Session lookup: valid, missing, expired, anonymous, and authenticated
  sessions.
- Authentication dependencies: missing, invalid or expired session, inactive
  user, anonymous session rejected.
- CSRF: missing, wrong, tampered value, and valid match.
- Login: success creates a new independent authenticated session and cookie;
  anonymous row is deleted; generic failure for wrong password and unknown
  email; inactive user is rejected.
- Registration: success creates the user transactionally, deletes the anonymous
  row, and creates an authenticated session; duplicate email is handled
  generically; failure creates no authenticated session.
- Logout: only `POST`, deletes only the current authenticated row, clears the
  cookie, and creates no anonymous session in the same response (section 15).
- Future tag ownership boundaries are tested in the tag increment with the same
  matrix.

Tests never create or modify `nfc_hub.db` and never depend on external services.
The existing 40 tests must continue to pass.

---

## 22. Explicitly Rejected Alternatives

1. **JWT tokens.** Rejected: revocation is hard, payloads are not immediately
   invalid, and shared signing secrets are unnecessary complexity. A server-side
   session provides immediate, deterministic revocation.
2. **Client-side signed cookies (Flask-style session).** Rejected: revocation
   requires versioned signed values, payload grows with session data, and a
   signing secret must be managed. A server-side session keeps client data and
   revocation simple.
3. **In-memory or Redis-only sessions.** Rejected: Redis belongs to a later
   deployment phase and would lose sessions on restart. Database sessions are
   persistent and consistent with the existing storage stack.
4. **bcrypt or PBKDF2.** Rejected in favor of Argon2id, the OWASP recommended
   memory-hard algorithm, whose reference library covers hashing, verification
   and rehash detection.
5. **Double-submit CSRF without server-side storage.** Rejected: it depends on
   the client presenting a second value and cannot be invalidated
   deterministically. A stored per-session token is stricter.
6. **Authentication by NFC tag UID or content.** Rejected explicitly in
   `AGENT.md` and `PROJECT.md`: UIDs and URLs are reproducible and must not be
   treated as proof of identity.
7. **Treating public NFC URLs as secret.** Rejected: a copied public URL must
   never grant management access. The public route only resolves public state.
8. **OAuth social login, email verification and recovery, MFA, per-role
   authorization.** Rejected for the MVP: all remain outside the current scope.
9. **Sliding session expiration.** Rejected for the initial implementation;
   absolute expiry is predictable, simple and sufficient.
10. **Client-side or SPA authentication.** Rejected: the initial frontend is
    server-rendered HTML forms with CSRF.

---

## Requirements for the Next Coding Increment

The next coding increment will include only:

- Centralized authentication, session and cookie settings.
- Password hashing and verification service (`argon2-cffi`, Argon2id).
- User registration.
- Session persistence model.
- Alembic migration for the `sessions` table.
- Login and logout workflows.
- CSRF protection required by those workflows.
- FastAPI dependencies for resolving and requiring the authenticated user.
- Automated tests for the implemented behavior.

It must not include: NFC tag persistence, ownership implementation, password
reset, account-management pages, rate limiting, MFA, OAuth, sliding sessions,
scheduled cleanup jobs, or unrelated frontend work.

---

## Features Planned for Later

- Rate limiting for login attempts.
- Sliding session renewal.
- Per-session client metadata (IP, user agent, device name).
- Scheduled or batch session cleanup.
- Password reset and recovery.
- Account-management pages and password change (which revokes all sessions).
- Multi-algorithm password support beyond automatic rehashing.
- Additional security headers beyond cookie attributes.
- Abuse detection for public tag routes.

---

## Known Design Notes

- Anonymous pre-authentication sessions use the 15-minute anonymous lifetime and
  are included in opportunistic and future batch cleanup.
- The exact redirect target for the authenticated management interface is a
  route detail, not an architectural decision, and is resolved during route
  implementation.
- If the Argon2id baseline parameters prove slow on the deployment hardware,
  higher values are allowed without an architectural change.
