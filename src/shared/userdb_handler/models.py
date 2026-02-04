from uuid import uuid4
from datetime import datetime
from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Column, String


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(sa_column=Column("email", String, unique=True, nullable=False))
    hashed_password: str
    tenant_id: str = Field(index=True)
    is_active: bool = Field(default=True)
    dept: str= Field()

    project: str= Field()

    clearance: int = Field()


class RefreshToken(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True)
    expires_at: datetime
    revoked: bool = Field(default=False)


class AuthorizationCode(SQLModel, table=True):
    """Temporary authorization codes for OAuth 2.1 PKCE flow."""
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    code: str = Field(index=True, unique=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str = Field(default="S256")
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
