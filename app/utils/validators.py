# app/utils/validators.py
"""
Input validation utilities.
"""
import re
from flask import request
import logging

logger = logging.getLogger(__name__)

def validate_input(text):
    """
    Validate text input to ensure it's not empty or malicious
    
    Args:
        text: Text to validate
        
    Returns:
        True if text is valid, False otherwise
    """
    if not text or len(text.strip()) < 10:
        return False
    if len(text) > 5000:  # Limit text length
        return False
    # Basic XSS prevention
    if re.search(r'<script|javascript:|data:', text, re.I):
        return False
    return True

def validate_file_url(url):
    """Validate a file URL"""
    if not url:
        return False, "URL is required"
    
    # Basic URL validation
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        return False, "Invalid URL format"
    
    # Check for supported file extensions
    supported_extensions = ['.pdf', '.docx', '.doc']
    if not any(url.lower().endswith(ext) for ext in supported_extensions):
        # If URL doesn't end with a supported extension, still allow it
        # because it might be a dynamic URL (e.g., Firebase storage URL)
        logger.warning(f"URL doesn't end with a supported extension: {url}")
    
    return True, ""

def validate_resume_data(data):
    """Validate resume data for generation"""
    required_fields = ['name', 'email', 'phone']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    if 'experience' not in data or not data['experience']:
        return False, "Resume must contain at least one experience entry"
    
    return True, ""

def validate_request_json(required_fields=None):
    """
    Decorator to validate request JSON data
    
    Args:
        required_fields: List of required fields in the JSON data
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return {"error": "Request must be JSON"}, 400
            
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator