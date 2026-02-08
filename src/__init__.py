from .shared.auth import config,dependencies,schemas,service,exceptions

from .shared.userdb_handler import User

settings = config.settings

AuthError = exceptions.AuthError
InvalidClientError =exceptions.InvalidClientError

AuthService = service.AuthService

UserRegister = schemas.UserRegister
UserResponse = schemas.UserResponse
UserLogin = schemas.UserLogin

AuthorizeResponse = schemas.AuthorizeResponse
AuthorizeRequest = schemas.AuthorizeRequest
TokenRequest = schemas.TokenRequest
TokenResponse = schemas. TokenResponse
TokenRevokeRequest = schemas.TokenRevokeRequest

get_auth_service = dependencies.get_auth_service
get_current_active_user = dependencies.get_current_active_user


__all__ = [

"settings",
"AuthError",
"AuthService",
"InvalidClientError",
"UserRegister",
"UserResponse",
"UserLogin",
"AuthorizeResponse",
"AuthorizeRequest",
"TokenRequest",
"TokenResponse",
"TokenRevokeRequest",
"get_auth_service",
"get_current_active_user",
"User",
]
