
"""Schemas for authentication requests and responses"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field



class RegisterRequest(BaseModel):
    """Data required to register a user"""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)



class LoginRequest(BaseModel):
    """Credentials required to authenticate a user"""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)



class UserResponse(BaseModel):
    """Public representation of an authenticated user"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr



class AuthResponse(BaseModel):
    """Authentication result containing public user and CSRF data"""

    user: UserResponse
    csrf_token: str
