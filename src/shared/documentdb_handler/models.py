from uuid import uuid4
from sqlmodel import Field, SQLModel  

class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    dept: str = Field()
    project: str = Field()
    clearance: int = Field()
    url: str = Field()
