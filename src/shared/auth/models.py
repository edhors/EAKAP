from sqlmodel import DateTime, Field,Index, SQLModel, String,Column,Boolean, Uuid
from pydantic  import EmailStr

class User(SQLModel, table=True):
    id: Uuid| None = Field(default=None, primary_key=True)
    email: EmailStr = Field(
        sa_column=Column("email", String, unique=True, nullable=False),
        max_length=255 
    )
    hashed_password: String
    tenant_id: String = Field(Index)
    is_active:Boolean = Field(default=True)

class RefreshToken(SQLModel, table=True):
    id: Uuid| None = Field(default=None, primary_key=True)
    user_id: Uuid| None = Field(default = None, foreign_key=User.id)
    token: String = Field(Index)
    expires_at: DateTime
    revoked:Boolean = Field(default=False)
