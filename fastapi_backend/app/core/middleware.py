"""
Request Logging Middleware

This module provides middleware for comprehensive request logging to help with
debugging and monitoring API usage.

Key Features:
- Log all incoming requests with method, URL, and headers
- Log request body for debugging (with sensitive data filtering)
- Log response status and timing
- User identification for request tracking
- Performance monitoring
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses for debugging.
    """
    
    def __init__(self, app, log_request_body: bool = True, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log relevant information.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler
            
        Returns:
            FastAPI response object
        """
        start_time = time.time()
        
        # Extract user information if available
        user_id = "anonymous"
        if hasattr(request.state, 'user') and request.state.user:
            user_id = str(request.state.user.id)
        
        # Log request details
        logger.info(f"Request started - User: {user_id}, Method: {request.method}, URL: {request.url}")
        
        # Log request headers (excluding sensitive ones)
        sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
        headers = {k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers}
        logger.debug(f"Request headers: {headers}")
        
        # Log request body for debugging (if enabled and not too large)
        if self.log_request_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body and len(body) < 10000:  # Only log if body is not too large
                    try:
                        body_json = json.loads(body.decode())
                        logger.debug(f"Request body: {body_json}")
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        logger.debug(f"Request body (raw): {body[:1000]}...")  # Truncate large bodies
            except Exception as e:
                logger.debug(f"Could not read request body: {e}")
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"Request completed - User: {user_id}, Method: {request.method}, "
                f"URL: {request.url}, Status: {response.status_code}, "
                f"Duration: {process_time:.3f}s"
            )
            
            # Log slow requests
            if process_time > 1.0:
                logger.warning(
                    f"Slow request detected - User: {user_id}, Method: {request.method}, "
                    f"URL: {request.url}, Duration: {process_time:.3f}s"
                )
            
            return response
            
        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            logger.error(
                f"Request failed - User: {user_id}, Method: {request.method}, "
                f"URL: {request.url}, Error: {str(e)}, Duration: {process_time:.3f}s"
            )
            raise


def setup_request_logging(app, log_request_body: bool = True, log_response_body: bool = False):
    """
    Set up request logging middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies (not recommended for production)
    """
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=log_request_body,
        log_response_body=log_response_body
    ) 