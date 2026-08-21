from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=15, max_length=128)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)  # can be email or username or OAuth provider email
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str


class AuthResponse(BaseModel):
    user: UserOut
    authenticated: bool = True
