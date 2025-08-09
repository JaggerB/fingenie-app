"""
Security fixes for Story 3.2 - AI Commentary Generation
Addresses critical security vulnerabilities identified in QA review.
"""

import re
import os
import logging
from typing import Optional, Tuple

# Security Configuration
MAX_FILENAME_LENGTH = 255
ALLOWED_FILE_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
MAX_FILE_SIZE_MB = 50

class SecurityUtils:
    """Utility class for security-related functions."""
    
    @staticmethod
    def sanitize_error_message(error_message: str) -> str:
        """
        Sanitize error messages to prevent sensitive information leakage.
        
        Args:
            error_message: Raw error message from exception or API
            
        Returns:
            str: Sanitized error message safe for user display
        """
        # Remove potential API keys (sk-...)
        sanitized = re.sub(r'sk-[a-zA-Z0-9]{10,}', '[API_KEY_REDACTED]', error_message)
        
        # Remove file paths
        sanitized = re.sub(r'/[a-zA-Z0-9/_\-\.]+', '[PATH_REDACTED]', sanitized)
        
        # Remove potential tokens or secrets
        sanitized = re.sub(r'token["\s]*[:=]["\s]*[a-zA-Z0-9]+', 'token=[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Remove email addresses 
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', sanitized)
        
        # Remove URLs
        sanitized = re.sub(r'https?://[^\s]+', '[URL_REDACTED]', sanitized)
        
        return sanitized
    
    @staticmethod
    def get_safe_error_message(error_type: str = "general") -> str:
        """
        Get predefined safe error messages for common scenarios.
        
        Args:
            error_type: Type of error (openai_client, file_processing, etc.)
            
        Returns:
            str: Safe error message for user display
        """
        safe_messages = {
            'openai_client': 'Failed to initialize AI service. Please check your configuration.',
            'file_processing': 'Error processing uploaded file. Please verify file format and try again.',
            'file_corrupted': 'Uploaded file appears to be corrupted. Please try uploading again.',
            'api_call': 'AI service temporarily unavailable. Using fallback analysis.',
            'general': 'An error occurred. Please try again or contact support.'
        }
        
        return safe_messages.get(error_type, safe_messages['general'])
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """
        Validate OpenAI API key format and basic security checks.
        
        Args:
            api_key: API key to validate
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not api_key:
            return False, "API key is required"
        
        # Check basic format (OpenAI keys start with 'sk-')
        if not api_key.startswith('sk-'):
            return False, "Invalid API key format"
        
        # Check minimum length
        if len(api_key) < 20:
            return False, "API key too short"
        
        # Check for suspicious characters
        if not re.match(r'^sk-[a-zA-Z0-9\-_]+$', api_key):
            return False, "API key contains invalid characters"
        
        return True, "Valid"
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded filename for security.
        
        Args:
            filename: Name of uploaded file
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not filename:
            return False, "Filename is required"
        
        # Check length
        if len(filename) > MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {MAX_FILENAME_LENGTH} characters)"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid filename: path traversal detected"
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            return False, "Filename contains invalid characters"
        
        # Check file extension
        if '.' not in filename:
            return False, "File must have an extension"
        
        extension = '.' + filename.split('.')[-1].lower()
        if extension not in ALLOWED_FILE_EXTENSIONS:
            return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/|?*\\\0]', '_', filename)
        
        # Remove path traversal
        sanitized = sanitized.replace('..', '_')
        
        # Limit length
        if len(sanitized) > MAX_FILENAME_LENGTH:
            name, extension = sanitized.rsplit('.', 1)
            max_name_length = MAX_FILENAME_LENGTH - len(extension) - 1
            sanitized = name[:max_name_length] + '.' + extension
        
        return sanitized
    
    @staticmethod
    def log_security_event(event_type: str, details: str, level: str = 'WARNING'):
        """
        Log security events with sanitized information.
        
        Args:
            event_type: Type of security event
            details: Event details (will be sanitized)
            level: Log level (WARNING, ERROR, CRITICAL)
        """
        logger = logging.getLogger('security')
        logger.setLevel(getattr(logging, level))
        
        # Sanitize details before logging
        sanitized_details = SecurityUtils.sanitize_error_message(details)
        
        log_message = f"SECURITY_EVENT: {event_type} - {sanitized_details}"
        
        if level == 'CRITICAL':
            logger.critical(log_message)
        elif level == 'ERROR':
            logger.error(log_message)
        else:
            logger.warning(log_message)


def secure_get_openai_client():
    """
    Secure version of get_openai_client with proper validation and error handling.
    
    Returns:
        OpenAI client instance or None if configuration invalid
    """
    from openai import OpenAI
    import streamlit as st
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Validate API key
    is_valid, validation_error = SecurityUtils.validate_api_key(api_key)
    if not is_valid:
        SecurityUtils.log_security_event('INVALID_API_KEY', validation_error, 'WARNING')
        st.error(SecurityUtils.get_safe_error_message('openai_client'))
        return None
    
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        # Log sanitized error for debugging
        SecurityUtils.log_security_event('OPENAI_CLIENT_INIT_FAILED', str(e), 'ERROR')
        
        # Show safe error to user
        st.error(SecurityUtils.get_safe_error_message('openai_client'))
        return None


def secure_log_api_failure(error_message: str, movement_data: dict = None):
    """
    Secure version of log_api_failure with sanitized logging.
    
    Args:
        error_message: Error message from API call
        movement_data: Optional movement data context
    """
    import logging
    
    # Configure security logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger('api_failures')
    
    # Sanitize error message before logging
    sanitized_error = SecurityUtils.sanitize_error_message(error_message)
    
    log_entry = f"OpenAI API failure: {sanitized_error}"
    if movement_data:
        # Only log non-sensitive account information
        account = movement_data.get('account', 'Unknown')
        # Sanitize account name too (in case it contains sensitive info)
        account = re.sub(r'[<>:"/|?*\\\0]', '_', account)[:50]  # Limit length
        log_entry += f" | Account: {account}"
    
    logger.error(log_entry)


def secure_file_upload_handler(uploaded_file) -> Tuple[bool, str, Optional[object]]:
    """
    Secure file upload handler with validation and sanitization.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        tuple: (success: bool, message: str, file_object: Optional[object])
    """
    import streamlit as st
    
    if uploaded_file is None:
        return False, "No file uploaded", None
    
    # Validate filename
    is_valid_name, name_error = SecurityUtils.validate_filename(uploaded_file.name)
    if not is_valid_name:
        SecurityUtils.log_security_event('INVALID_FILENAME', f"File: {uploaded_file.name}, Error: {name_error}")
        return False, f"Invalid filename: {name_error}", None
    
    # Check file size
    file_size = len(uploaded_file.getvalue())
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    
    if file_size > max_size_bytes:
        SecurityUtils.log_security_event('FILE_TOO_LARGE', f"Size: {file_size} bytes, Limit: {max_size_bytes} bytes")
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB", None
    
    if file_size == 0:
        return False, "Uploaded file is empty", None
    
    # Log successful upload
    sanitized_name = SecurityUtils.sanitize_filename(uploaded_file.name)
    SecurityUtils.log_security_event('FILE_UPLOAD_SUCCESS', f"File: {sanitized_name}, Size: {file_size} bytes", 'INFO')
    
    return True, f"File uploaded successfully: {sanitized_name}", uploaded_file


# Security test functions for validation
def test_security_utils():
    """Test security utility functions."""
    print("Testing Security Utils...")
    
    # Test error sanitization
    dangerous_error = "API key sk-abc123def456 failed at /home/user/app.py"
    sanitized = SecurityUtils.sanitize_error_message(dangerous_error)
    print(f"Original: {dangerous_error}")
    print(f"Sanitized: {sanitized}")
    assert '[API_KEY_REDACTED]' in sanitized
    assert '[PATH_REDACTED]' in sanitized
    
    # Test API key validation
    valid_key = "sk-abc123def456ghi789"
    is_valid, _ = SecurityUtils.validate_api_key(valid_key)
    assert is_valid
    
    invalid_key = "invalid-key"
    is_valid, _ = SecurityUtils.validate_api_key(invalid_key)
    assert not is_valid
    
    # Test filename validation
    valid_filename = "financial_data.xlsx"
    is_valid, _ = SecurityUtils.validate_filename(valid_filename)
    assert is_valid
    
    dangerous_filename = "../../../etc/passwd"
    is_valid, _ = SecurityUtils.validate_filename(dangerous_filename)
    assert not is_valid
    
    print("✅ All security tests passed!")


if __name__ == "__main__":
    test_security_utils()