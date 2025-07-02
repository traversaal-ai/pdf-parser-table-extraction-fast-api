"""
Custom exception classes for the API and services.
"""

class ServiceError(Exception):
    """Base exception for service errors."""
    pass

class DoclingServiceError(ServiceError):
    """Exception for Docling extraction errors."""
    pass

class LlamaParseServiceError(ServiceError):
    """Exception for LlamaParse extraction errors."""
    pass

class UnstructuredServiceError(ServiceError):
    """Exception for Unstructured extraction errors."""
    pass 