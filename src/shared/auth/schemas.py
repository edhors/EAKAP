from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Registration
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    tenant_id: str
    dept: str
    project: str
    clearance: int

class UserResponse(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_active: bool


# Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Authorization request
class AuthorizeRequest(BaseModel):
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str = "S256"
    state: Optional[str] = None


# Authorization response
class AuthorizeResponse(BaseModel):
    code: str
    state: Optional[str] = None


# Token request
class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: str


# Token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


# Token revoke
class TokenRevokeRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = None


# JWT payload structure
class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    tenant_id: str
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str  # "access" or "refresh"
