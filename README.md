# fastapply-resumify
## Installation

1. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Download the spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```




## Running the Application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Setup Redis:
   ```bash
   python scripts/setup_redis.py
   ```

3. Start the application:
   ```bash
   gunicorn app.wsgi:app -c gunicorn.conf.py
   ```

## Health Check and Monitoring

We've added a `/health` endpoint that provides:

- Application status
- Redis connection status
- Cache statistics

This helps with monitoring the application and Redis memory usage.