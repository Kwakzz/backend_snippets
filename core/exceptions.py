from fastapi import HTTPException, status
from typing import Any, Dict, Optional
from fastapi import status
from enum import Enum


class ErrorCode(Enum):
    # GENERIC 400 ERROR
    HTTP_ERROR = 'HTTP_ERROR'

    # VALIDATION ERROR CODES (STATUS CODE: 422)
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    INVALID_FIELD_TYPE = 'INVALID_FIELD_TYPE'
    FIELD_TOO_SHORT = 'FIELD_TOO_SHORT'
    FIELD_TOO_LONG = 'FIELD_TOO_LONG'
    VALUE_OUT_OF_RANGE = 'VALUE_OUT_OF_RANGE'
    UNSUPPORTED_FILE_TYPE = 'UNSUPPORTED_FILE_TYPE'
    CONTENT_NOT_ALLOWED = 'CONTENT_NOT_ALLOWED'

    # BUSINESS LOGIC ERROR CODES (STATUS CODE: 422)
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    DUPLICATE_ENTRY = 'DUPLICATE_ENTRY'
    UNREGISTERED_EMAIL = 'UNREGISTERED_EMAIL'
    WRONG_PASSWORD = 'WRONG_PASSWORD'
    VALUES_DONT_MATCH = 'VALUES_DONT_MATCH'
    ALREADY_VERIFIED = 'ALREADY_VERIFIED'

    # AUTHENTICATION_ERROR (STATUS CODE: 401)
    UNAUTHENTICATED = 'UNAUTHENTICATED'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    INVALID_TOKEN = 'INVALID_TOKEN'

    # RESOURCE ERROR CODES (STATUS CODE: 404 or 403)
    RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND'
    RESOURCE_FORBIDDEN = 'RESOURCE_FORBIDDEN'
    INVALID_ENDPOINT = 'INVALID_ENDPOINT'

    # REQUEST ERROR CODES (STATUS CODE: 400 or 405)
    BAD_REQUEST = 'BAD_REQUEST'
    SYNTAX_ERROR = 'SYNTAX_ERROR'
    REQUIRED_FIELD_MISSING = 'REQUIRED_FIELD_MISSING'
    METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED'

    # TOO MANY REQUESTS (STATUS CODE: 429)
    TOO_MANY_REQUESTS = 'TOO_MANY_REQUESTS'

    # SERVER ERRORS (STATUS CODE: 5xx)
    INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
        
        
class ValidationError(HTTPException):
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCode.VALIDATION_ERROR.value,
        data: Optional[Dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": False,
                "error_code": error_code,
                "message": message,
                "data":data
            }
        )


class BadRequest(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": False,
                "error_code": ErrorCode.BAD_REQUEST.value,
                "message": message,
            }
        )
        
        
class AuthenticationFailedError(HTTPException):
    def __init__(
        self, 
        message: str,
        error_code: str = ErrorCode.UNAUTHENTICATED.value
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": False,
                "error_code": error_code,
                "message": message,
            }
        )
        

class ForbiddenError(HTTPException):
    def __init__(
        self,
        message: str = "You're not allowed to access this resource.",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": False,
                "error_code": ErrorCode.RESOURCE_FORBIDDEN.value,
                "message": message,
            }
        )

        
class ResourceNotFoundError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": False,
                "error_code": ErrorCode.RESOURCE_NOT_FOUND.value,
                "message": message,
            }
        )
        

class InternalServerError(HTTPException):
    def __init__(self, message: str = "Something went wrong. Please try again later"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": False,
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": message,
            }
        )