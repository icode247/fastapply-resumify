"""
WSGI entry point for the application.
"""
import os
from app import create_app
from app.config import Config

app = create_app(Config)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)