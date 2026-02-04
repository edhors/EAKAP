from .database import get_session,init_db
from .service import UserService as db
import pytest
init_db()
sessionGroup = get_session()
session = next(sessionGroup)
db_session= db(session=session)
class TestUser:

    def test_create_user(self):
        user = db_session.create_user(email="abcabc.com",hashed_password="123",tenant_id="123",dept="hr",project="proij1",clearance=12)
        assert user is not None
       
