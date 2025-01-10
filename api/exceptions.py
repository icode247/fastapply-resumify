class APIError(Exception):
    """Raised when the API call fails"""
    pass

class ConversionError(Exception):
    """Raised when LaTeX to HTML conversion fails"""
    pass 