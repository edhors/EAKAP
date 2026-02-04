import database

database.init_db()

sessionGroup = database.get_session()

session = next(sessionGroup)


