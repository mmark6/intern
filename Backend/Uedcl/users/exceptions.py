"""
Custom exception handler for REST API.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for API errors.
    Provides consistent error response format and logs security issues.
    """
    response = exception_handler(exc, context)

    if response is None:
        # Log unexpected errors
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Unhandled exception: {str(exc)}\nTraceback: {tb}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred', 'detail': str(exc)},
            status=500
        )

    # Log authentication failures
    if response.status_code == 401:
        logger.warning(f"Authentication failed: {context.get('request').path}")
    
    # Log authorization failures
    if response.status_code == 403:
        logger.warning(
            f"Permission denied for user {context.get('request').user} at {context.get('request').path}"
        )
    
    # Log validation errors
    if response.status_code == 400:
        logger.info(f"Validation error at {context.get('request').path}: {response.data}")

    # Customize error response format
    if isinstance(response.data, dict):
        response.data = {
            'success': False,
            'status_code': response.status_code,
            'errors': response.data,
            'message': get_error_message(response.status_code)
        }
    
    return response


def get_error_message(status_code):
    """Get user-friendly error message for status code."""
    messages = {
        400: 'Bad request. Please check your input.',
        401: 'Unauthorized. Please log in.',
        403: 'Permission denied. You do not have access.',
        404: 'Resource not found.',
        429: 'Too many requests. Please try again later.',
        500: 'Internal server error. Please try again later.',
    }
    return messages.get(status_code, 'An error occurred')
