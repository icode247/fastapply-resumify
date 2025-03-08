import logging
import logging.handlers
import os
import json
import traceback
from datetime import datetime
import sys

# Create a custom formatter that mimics Winston's JSON format
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
            
        return json.dumps(log_record)


class CustomLogger:
    """A custom logger class with Winston-like functionality"""
    
    def __init__(self, name, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.setup_handlers()
        
    # def setup_handlers(self):
    #     # Clear any existing handlers
    #     if self.logger.handlers:
    #         self.logger.handlers = []
            
    #     # Create console handler
    #     console_handler = logging.StreamHandler(sys.stdout)
    #     console_handler.setFormatter(JsonFormatter())
    #     self.logger.addHandler(console_handler)
        
    #     # Create file handler for error logs
    #     log_dir = os.environ.get('LOG_DIR', 'logs')
    #     os.makedirs(log_dir, exist_ok=True)
        
    #     error_handler = logging.handlers.RotatingFileHandler(
    #         os.path.join(log_dir, 'error.log'),
    #         maxBytes=10485760,  # 10MB
    #         backupCount=5
    #     )
    #     error_handler.setLevel(logging.ERROR)
    #     error_handler.setFormatter(JsonFormatter())
    #     self.logger.addHandler(error_handler)
        
    #     # Create file handler for application logs
    #     app_handler = logging.handlers.RotatingFileHandler(
    #         os.path.join(log_dir, 'app.log'),
    #         maxBytes=10485760,  # 10MB
    #         backupCount=5
    #     )
    #     app_handler.setFormatter(JsonFormatter())
    #     self.logger.addHandler(app_handler)

    def setup_handlers(self):
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers = []
            
        # Always add console handler (Heroku captures this)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(console_handler)
        
        # Only add file handlers in development environment
        if os.environ.get('FLASK_ENV') != 'production':
            # Create log directory
            log_dir = os.environ.get('LOG_DIR', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Add file handlers for local development
            error_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_dir, 'error.log'),
                maxBytes=10485760,
                backupCount=5
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(error_handler)
            
            app_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10485760,
                backupCount=5
            )
            app_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(app_handler)
        
    def log(self, level, message, extra=None):
        """Log a message with optional extra data"""
        extra_record = {'extra_data': extra} if extra else {}
        self.logger.log(level, message, extra=extra_record)
    
    def info(self, message, extra=None):
        """Log an info message"""
        self.log(logging.INFO, message, extra)
    
    def error(self, message, extra=None, exc_info=None):
        """Log an error message"""
        if exc_info is True:
            exc_info = sys.exc_info()
        self.logger.error(message, exc_info=exc_info, extra={'extra_data': extra} if extra else {})
    
    def warn(self, message, extra=None):
        """Log a warning message"""
        self.log(logging.WARNING, message, extra)
    
    def debug(self, message, extra=None):
        """Log a debug message"""
        self.log(logging.DEBUG, message, extra)
    
    def critical(self, message, extra=None, exc_info=None):
        """Log a critical message"""
        if exc_info is True:
            exc_info = sys.exc_info()
        self.logger.critical(message, exc_info=exc_info, extra={'extra_data': extra} if extra else {})


# Create a Flask request logger middleware
class RequestLogger:
    """Middleware to log HTTP requests in Flask"""
    
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        
    def before_request(self):
        """Log incoming request"""
        from flask import request, g
        import time
        
        # Store start time
        g.start_time = time.time()
        
        # Log request details
        self.logger.info(f"Request started: {request.method} {request.path}", {
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string,
            'content_type': request.content_type,
            'content_length': request.content_length
        })
        
    def after_request(self, response):
        """Log response details"""
        from flask import request, g
        import time
        
        # Calculate request duration
        duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
        
        # Log response details
        self.logger.info(f"Request completed: {request.method} {request.path} {response.status_code}", {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': int(duration * 1000),
            'content_length': response.content_length,
            'content_type': response.content_type
        })
        
        return response


# Create the main application logger
def create_app_logger(name='app'):
    """Create the main application logger"""
    return CustomLogger(name)