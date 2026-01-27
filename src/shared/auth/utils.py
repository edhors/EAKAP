from pwdlib import PasswordHash
from jose import jwt
import hashlib,base64,secrets
from typing import Tuple

#NOTE: secret algorithm and key in env are needed. Use pydantic and config to set them up later
def get_password_hash(password:str)-> str:
    password_hash = PasswordHash.recommended()

    hash = password_hash.hash(password)
    return hash
def verify_password(plain_password:str,hashed_password:str)->bool:

    password_hash = PasswordHash.recommended()
    verified = password_hash.verify(plain_password,hashed_password)

    return verified


def create_access_token(new_payload: dict):
    token = jwt.encode(new_payload,key="sample key",algorithm='SHA256')
    
    return token

#
def creat_refresh_token(payload_with_jwt: dict):
    token = jwt.encode(payload_with_jwt,key="sample key",algorithm='SHA256')
    
    return token


#NOTE: Curtousy of RomeoDespres, as an initial pkce code
def generate_code_verifier(length: int = 128) -> str:
    """Return a random PKCE-compliant code verifier.

    Parameters
    ----------
    length : int
        Code verifier length. Must verify `43 <= length <= 128`.

    Returns
    -------
    code_verifier : str
        Code verifier.

    Raises
    ------
    ValueError
        When `43 <= length <= 128` is not verified.
    """
    if not 43 <= length <= 128:
        msg = 'Parameter `length` must verify `43 <= length <= 128`.'
        raise ValueError(msg)
    code_verifier = secrets.token_urlsafe(96)[:length]
    return code_verifier


def generate_pkce_pair(code_verifier_length: int = 128) -> Tuple[str, str]:
    """Return random PKCE-compliant code verifier and code challenge.

    Parameters
    ----------
    code_verifier_length : int
        Code verifier length. Must verify
        `43 <= code_verifier_length <= 128`.

    Returns
    -------
    code_verifier : str
    code_challenge : str

    Raises
    ------
    ValueError
        When `43 <= code_verifier_length <= 128` is not verified.
    """
    if not 43 <= code_verifier_length <= 128:
        msg = 'Parameter `code_verifier_length` must verify '
        msg += '`43 <= code_verifier_length <= 128`.'
        raise ValueError(msg)
    code_verifier = generate_code_verifier(code_verifier_length)
    code_challenge = get_code_challenge(code_verifier)
    return code_verifier, code_challenge


def get_code_challenge(code_verifier: str) -> str:
    """Return the PKCE-compliant code challenge for a given verifier.

    Parameters
    ----------
    code_verifier : str
        Code verifier. Must verify `43 <= len(code_verifier) <= 128`.

    Returns
    -------
    code_challenge : str
        Code challenge that corresponds to the input code verifier.

    Raises
    ------
    ValueError
        When `43 <= len(code_verifier) <= 128` is not verified.
    """
    if not 43 <= len(code_verifier) <= 128:
        msg = 'Parameter `code_verifier` must verify '
        msg += '`43 <= len(code_verifier) <= 128`.'
        raise ValueError(msg)
    hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii')[:-1]
    return code_challenge
