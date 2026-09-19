
import hashlib
import re

import nfc_hub.core.tokens as token_module
from nfc_hub.core.tokens import (
    CSRF_TOKEN_BYTES,
    SESSION_TOKEN_BYTES,
    generate_csrf_token,
    generate_session_token,
    hash_session_token,
    verify_csrf_token,
)

URLSAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class TestSessionTokenGeneration:
    def test_uses_configured_number_of_random_bytes(self, monkeypatch):
        requested_bytes = []

        def fake_token_urlsafe(number_of_bytes):
            requested_bytes.append(number_of_bytes)
            return "generated-session-token"

        monkeypatch.setattr(
            token_module.secrets,
            "token_urlsafe",
            fake_token_urlsafe,
        )

        token = generate_session_token()

        assert token == "generated-session-token"
        assert requested_bytes == [SESSION_TOKEN_BYTES]


    def test_generates_url_safe_token(self):
        token = generate_session_token()

        assert URLSAFE_TOKEN_PATTERN.fullmatch(token)


    def test_generates_different_tokens(self):
        first_token = generate_session_token()
        second_token = generate_session_token()

        assert first_token != second_token



class TestSessionTokenHashing:
    def test_returns_expected_sha256_hash(self):
        token = "session-token"

        expected_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        assert hash_session_token(token) == expected_hash


    def test_returns_64_character_hexadecimal_hash(self):
        token_hash = hash_session_token("session-token")

        assert len(token_hash) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", token_hash)


    def test_same_token_produces_same_hash(self):
        assert hash_session_token("session-token") == hash_session_token(
            "session-token"
        )


    def test_different_tokens_produce_different_hashes(self):
        assert hash_session_token("first-token") != hash_session_token(
            "second-token"
        )



class TestCsrfTokenGeneration:
    def test_uses_configured_number_of_random_bytes(self, monkeypatch):
        requested_bytes = []


        def fake_token_urlsafe(number_of_bytes):
            requested_bytes.append(number_of_bytes)
            return "generated-csrf-token"

        monkeypatch.setattr(
            token_module.secrets,
            "token_urlsafe",
            fake_token_urlsafe,
        )

        token = generate_csrf_token()

        assert token == "generated-csrf-token"
        assert requested_bytes == [CSRF_TOKEN_BYTES]


    def test_generates_url_safe_token(self):
        token = generate_csrf_token()

        assert URLSAFE_TOKEN_PATTERN.fullmatch(token)


    def test_generates_different_tokens(self):
        first_token = generate_csrf_token()
        second_token = generate_csrf_token()

        assert first_token != second_token



class TestCsrfTokenVerification:
    def test_matching_tokens_are_valid(self):
        assert verify_csrf_token("csrf-token", "csrf-token") is True


    def test_different_tokens_are_invalid(self):
        assert verify_csrf_token("received-token", "expected-token") is False


    def test_unicode_input_does_not_raise_error(self):
        assert verify_csrf_token("token-cl", "token-cl") is True
