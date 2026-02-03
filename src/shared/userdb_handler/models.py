
from sqlmodel import DateTime, Field,Index, SQLModel, String,Column,Boolean, Uuid
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


#FIX: Needs pydantic checks and all-- implement
#TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
#TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

engine = create_engine(
     "sqlite+libsql:///embedded.db",
     connect_args={
         "auth_token": TURSO_AUTH_TOKEN,
         "sync_url": TURSO_DATABASE_URL,
     },
)
