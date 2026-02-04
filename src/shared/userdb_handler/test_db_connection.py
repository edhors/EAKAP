from .database import get_session,init_db

def test_db_connection():

        init_db()

        sessionGroup = get_session()

        session = next(sessionGroup)
        assert type(session).__name__ == "Session"
