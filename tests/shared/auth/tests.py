from src.shared.auth import utils

password = "abdhalla"

hashed_password = utils.get_password_hash(password=password)

if(utils.verify_password(plain_password=password, hashed_password=hashed_password)):
    print("Works")
else:
    print("Not really")
