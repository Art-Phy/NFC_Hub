
import pytest
from pydantic import ValidationError

from nfc_hub.models import User
from nfc_hub.schemas.auth import (
    AuthResponse,
    RegisterRequest,
    UserResponse,
)



class TestRegisterRequest:
    def test_accepts_valid_registration_data(self):
        request = RegisterRequest(
            email="user@example.com",
            password="secure-password",
        )

        assert request.email == "user@example.com"
        assert request.password == "secure-password"


    def test_normalizes_email_domain(self):
        request = RegisterRequest(
            email="user@EXAMPLE.COM",
            password="secure-password",
        )

        assert request.email == "user@example.com"


    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="secure-password",
            )


    def test_rejects_password_shorter_than_eight_characters(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="short",
            )


    def test_accepts_password_at_minimum_length(self):
        request = RegisterRequest(
            email="user@example.com",
            password="12345678",
        )

        assert request.password == "12345678"


    def test_rejects_password_longer_than_128_characters(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="a" * 129,
            )


    def test_does_not_strip_password_whitespace(self):
        request = RegisterRequest(
            email="user@example.com",
            password="  password  ",
        )

        assert request.password == "  password  "



class TestUserResponse:
    def test_builds_response_from_user_model(self):
        user = User(
            id=42,
            email="user@example.com",
            password_hash="secret-password-hash",
        )

        response = UserResponse.model_validate(user)

        assert response.id == 42
        assert response.email == "user@example.com"


    def test_does_not_expose_password_hash(self):
        user = User(
            id=42,
            email="user@example.com",
            password_hash="secret-password-hash",
        )

        response = UserResponse.model_validate(user)

        assert "password_hash" not in response.model_dump()



class TestAuthResponse:
    def test_contains_public_user_and_csrf_token(self):
        response = AuthResponse(
            user=UserResponse(
                id=42,
                email="user@example.com",
            ),
            csrf_token="csrf-token",
        )

        assert response.model_dump(mode="json") == {
            "user": {
                "id": 42,
                "email": "user@example.com",
            },
            "csrf_token": "csrf-token",
        }


    def test_does_not_contain_session_token(self):
        response = AuthResponse(
            user=UserResponse(
                id=42,
                email="user@example.com",
            ),
            csrf_token="csrf-token",
        )

        assert "session_token" not in response.model_dump()
