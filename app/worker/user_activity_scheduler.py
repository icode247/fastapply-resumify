import logging
import os
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.info(f"Loaded .env file from: {dotenv_path}")
else:
    logging.warning(f".env file not found at: {dotenv_path}. Using system environment variables.")

# Environment variable for Vercel rate limit reset endpoint
RATE_LIMIT_RESET_URL = os.environ.get('RATE_LIMIT_RESET_URL')
logging.info(f"RATE_LIMIT_RESET_URL loaded: {RATE_LIMIT_RESET_URL}")

scheduler = BlockingScheduler(timezone="UTC")


def call_rate_limit_reset_endpoint():
    """
    Calls the Vercel API endpoint to reset rate limits.
    Runs every 24 hours at midnight UTC.
    """
    logging.info("Starting rate limit reset job...")
    
    if not RATE_LIMIT_RESET_URL:
        logging.error("RATE_LIMIT_RESET_URL environment variable not set. Skipping job.")
        return
    
    try:
        logging.info(f"Calling rate limit reset endpoint: {RATE_LIMIT_RESET_URL}")
        
        response = requests.post(
            RATE_LIMIT_RESET_URL,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logging.info(f"Rate limit reset successful. Response: {response.text}")
        else:
            logging.error(f"Rate limit reset failed. Status: {response.status_code}, Response: {response.text}")
            
    except requests.exceptions.Timeout:
        logging.error(f"Timeout calling rate limit reset endpoint: {RATE_LIMIT_RESET_URL}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling rate limit reset endpoint: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during rate limit reset: {str(e)}", exc_info=True)
    
    logging.info("Rate limit reset job finished.")


if __name__ == "__main__":
    logging.info("Rate Limit Reset Scheduler starting up...")
    
    if not RATE_LIMIT_RESET_URL:
        logging.critical("RATE_LIMIT_RESET_URL not configured. Please set it in your .env file.")
        logging.critical("Example: RATE_LIMIT_RESET_URL=https://your-app.vercel.app/api/reset-rate-limit")
        exit(1)
    
    # Schedule the rate limit reset job to run every day at midnight UTC
    scheduler.add_job(
        call_rate_limit_reset_endpoint,
        'cron',
        hour=0,
        minute=0,
        misfire_grace_time=300
    )
    logging.info("Scheduled 'call_rate_limit_reset_endpoint' job for 00:00 UTC daily.")
    
    logging.info("Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped by user.")
    except Exception as e:
        logging.critical(f"Scheduler failed to start or crashed: {e}", exc_info=True)
