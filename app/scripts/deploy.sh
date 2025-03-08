#!/bin/bash
# Deployment script for Resumify API

set -e  # Exit on error

# Configuration
APP_NAME="resumify-api"
DEPLOY_ENV=${1:-"production"}  # Default to production if no argument provided

echo "===== Starting deployment of $APP_NAME to $DEPLOY_ENV ====="

# Ensure we have the latest code
echo "Pulling latest code..."
git pull origin main

# Install or update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup Redis
echo "Setting up Redis..."
python scripts/setup_redis.py

# Download spaCy model if needed
echo "Ensuring spaCy model is installed..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs

# Setup environment specific configuration
if [ "$DEPLOY_ENV" == "production" ]; then
  echo "Setting up production environment..."
  export FLASK_ENV="production"
  # Additional production-specific setup
  export REDIS_MAX_MEMORY="25mb"  # Limit Redis memory in production
  
  # Set production logging level
  export LOG_LEVEL="ERROR"
elif [ "$DEPLOY_ENV" == "staging" ]; then
  echo "Setting up staging environment..."
  export FLASK_ENV="staging"
  # Additional staging-specific setup
  export REDIS_MAX_MEMORY="20mb"  # Smaller cache for staging
  
  # Set staging logging level
  export LOG_LEVEL="INFO"
else
  echo "Setting up development environment..."
  export FLASK_ENV="development"
  # Additional development-specific setup
  export REDIS_MAX_MEMORY="10mb"  # Smaller cache for development
  
  # Set development logging level
  export LOG_LEVEL="DEBUG"
fi

# Check for Redis connection
echo "Checking Redis connection..."
if ! python -c "import redis; redis.from_url(\"${REDIS_URL:-redis://localhost:6379/0}\").ping()"; then
  echo "WARNING: Could not connect to Redis. Cache functionality will be disabled."
fi

# Start the application using gunicorn
echo "Starting the application..."
if [ "$DEPLOY_ENV" == "production" ]; then
  # Use more workers in production
  gunicorn app.wsgi:app -c gunicorn.conf.py --workers=4
else
  # Use fewer workers in other environments
  gunicorn app.wsgi:app -c gunicorn.conf.py --workers=2
fi

echo "===== Deployment completed ====="