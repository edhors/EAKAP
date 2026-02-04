from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select
from .models import User, RefreshToken


class UserService:
    """Service for user CRUD operations."""

    def __init__(self, session: Session):
        self._session = session

    def create_user(self, email: str, hashed_password: str, tenant_id: str, dept:str, project:str, clearance:int) -> User:
        """Create a new user."""
        user = User(email=email, hashed_password=hashed_password, tenant_id=tenant_id, dept=dept,project=project,clearance=clearance)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        statement = select(User).where(User.email == email)
        return self._session.exec(statement).first()

    def get_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get all users for a tenant."""
        statement = select(User).where(User.tenant_id == tenant_id)
        return list(self._session.exec(statement).all())

    def get_users_by_project(self, project: str) -> List[User]:
        """Get all users for a project."""
        statement = select(User).where(User.project == project)
        return list(self._session.exec(statement).all())


    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        self._session.delete(user)
        self._session.commit()
        return True


class TokenService:
    """Service for refresh token operations."""

    def __init__(self, session: Session):
        self._session = session

    def create_token(self, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        """Create a new refresh token."""
        refresh_token = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
        self._session.add(refresh_token)
        self._session.commit()
        self._session.refresh(refresh_token)
        return refresh_token

    def get_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        statement = select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.revoked == False,
        )
        return self._session.exec(statement).first()

    def get_tokens_by_user(self, user_id: str) -> List[RefreshToken]:
        """Get all active tokens for a user."""
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
        return list(self._session.exec(statement).all())

    def revoke_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        refresh_token = self.get_token(token)
        if not refresh_token:
            return False
        refresh_token.revoked = True
        self._session.add(refresh_token)
        self._session.commit()
        return True

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user. Returns count of revoked tokens."""
        tokens = self.get_tokens_by_user(user_id)
        for token in tokens:
            token.revoked = True
            self._session.add(token)
        self._session.commit()
        return len(tokens)
