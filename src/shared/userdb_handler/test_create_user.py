from service import UserService
import database
email = "nate@abc.com"
password = "1234567"
dept = "HR"
project = "test"
clearance = 12
tenant_id = "nate@123"


database.init_db()

sess = database.get_session()
session = next(sess)
user_service = UserService(session)
user = UserService.create_user(user_service,email=email,hashed_password=password,tenant_id=tenant_id,dept=dept,project=project,clearance=clearance)


print(UserService.get_user_by_email(user_service,"nate@abc.com"))
