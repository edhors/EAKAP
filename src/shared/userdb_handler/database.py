from typing import Generator
from sqlmodel import Session, create_engine, SQLModel


engine = create_engine(
    "sqlite:///embedded.db",
   )


def init_db() -> None:
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection."""
    with Session(engine) as session:
        yield session
