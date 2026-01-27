from pwdlib import PasswordHash

def get_password_hash(password:str)-> str:
    password_hash = PasswordHash.recommended()

    hash = password_hash.hash(password)
    return hash
def verify_password(plain_password:str,hashed_password:str)->bool:

    password_hash = PasswordHash.recommended()
    verified = password_hash.verify(plain_password,hashed_password)

    return verified




