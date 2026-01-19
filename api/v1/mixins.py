from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger(__name__)


class SuccessErrorResponseMixin:
    @staticmethod
    def success(data=None, status_code=200):
        return Response({
            "success": True,
            "data": data
        }, status=status_code)

    @staticmethod
    def error(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
        logger.warning(f"API error [{code}]: {message} | details={details}")
        return Response({
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            }
        }, status=status_code)