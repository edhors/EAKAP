from pwdlib import PasswordHash
from jose import jwt, JWTError
import hashlib, base64, secrets
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from .config import settings


def get_password_hash(password: str) -> str:
    """Hash password using pwdlib's recommended algorithm."""
    password_hash = PasswordHash.recommended()
    hash = password_hash.hash(password)
    return hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    password_hash = PasswordHash.recommended()
    verified = password_hash.verify(plain_password, hashed_password)
    return verified


def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token with proper expiration."""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
        "type": "refresh",
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


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
