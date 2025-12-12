"""
Custom exceptions for the service layer.

Provides specific exception types for different error scenarios,
making error handling more precise and informative for API consumers.
"""

from typing import Any, Dict, Optional


class ServiceError(Exception):
    """
    Base exception for all service layer errors.
    
    All service-specific exceptions inherit from this to enable
    consistent error handling at the API layer.
    """
    pass


class NotFoundError(ServiceError):
    """
    Resource not found in database.
    
    Raised when attempting to retrieve or modify a resource
    that doesn't exist or is owned by a different user.
    """
    
    def __init__(self, resource_type: str, resource_id: str):
        """
        Initialize not found error.
        
        Args:
            resource_type: Type of resource (e.g., "Thought", "Task")
            resource_id: ID of the missing resource
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            f"{resource_type} with ID '{resource_id}' not found or "
            f"you don't have permission to access it."
        )


class UnauthorizedError(ServiceError):
    """
    User doesn't have permission to access resource.
    
    Raised when user attempts to access or modify a resource
    they don't own.
    """
    
    def __init__(self, resource_type: str, user_id: str):
        """
        Initialize unauthorized error.
        
        Args:
            resource_type: Type of resource being accessed
            user_id: ID of the user attempting access
        """
        self.resource_type = resource_type
        self.user_id = user_id
        super().__init__(
            f"User '{user_id}' is not authorized to access this {resource_type}."
        )


class InvalidDataError(ServiceError):
    """
    Data validation failed at service layer.
    
    Raised when business logic validation fails beyond what
    Pydantic catches at the API layer.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize invalid data error.
        
        Args:
            message: Human-readable error description
            details: Optional dict with field-specific error details
        """
        self.details = details or {}
        super().__init__(message)


class DatabaseError(ServiceError):
    """
    Database operation failed.
    
    Wraps SQLAlchemy exceptions to provide cleaner error
    messages to API consumers.
    """
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize database error.
        
        Args:
            message: Human-readable error description
            original_error: Original SQLAlchemy exception (for logging)
        """
        self.original_error = original_error
        super().__init__(message)


class ConflictError(ServiceError):
    """
    Operation conflicts with existing data.
    
    Raised when attempting to create a resource that would
    violate uniqueness constraints or business rules.
    """
    
    def __init__(self, message: str, conflicting_field: Optional[str] = None):
        """
        Initialize conflict error.
        
        Args:
            message: Human-readable error description
            conflicting_field: Field that caused the conflict
        """
        self.conflicting_field = conflicting_field
        super().__init__(message)
