"""
Custom Exception Handler for Django REST Framework.
Ensures standardized JSON response formats for API errors.
"""
from typing import Optional, Any, Dict
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Custom exception handler to format error responses consistently.
    
    Args:
        exc (Exception): The raised exception.
        context (Dict[str, Any]): Context dict from DRF view.
        
    Returns:
        Optional[Response]: Standardized Response object or None.
    """
    response = exception_handler(exc, context)

    if response is not None:
        customized_response = {
            "status": "error",
            "code": response.status_code,
            "message": "Terjadi kesalahan pada permintaan Anda.",
            "errors": response.data,
        }
        response.data = customized_response

    return response
