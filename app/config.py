"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration"""
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp')
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # Redis settings
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_MAX_MEMORY = os.environ.get('REDIS_MAX_MEMORY', '25mb')
    REDIS_EXPIRATION = int(os.environ.get('REDIS_EXPIRATION', 1800))  # 30 minutes default
    
    # API integration settings
    HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
