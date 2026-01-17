from pydantic import BaseModel
from typing import Any, Optional, Dict,  List


class SuccessResponse(BaseModel):
    status: bool = True
    data: Optional[Any] = None
    message: str  
    meta: Optional[Dict[str, Any]] = None  # Optional metadata (e.g., pagination info)
        
        
class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    status: bool = False
    error_code: str  
    message: str  
    data: Optional[Dict[str, List[ErrorDetail]]] = None  # Validation errors or additional details
    
    

def success_response(
    data: Any = None, 
    message: str = "Request successful", 
    meta: Optional[Dict[str, Any]] = None
) -> SuccessResponse:
    return SuccessResponse(
        status=True,
        data=data,
        message=message,
        meta=meta
    )