import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
import redis

import os
from dotenv import load_dotenv

# Determine the path to the .env file (assuming it's in the project root)
# If scheduler.py is in app/ and .env is in resumify/, then .env is one level up.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 

# Check if the .env file exists at that path
if os.path.exists(dotenv_path):
    print(f"Loading .env file from: {dotenv_path}") # For debugging
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f".env file not found at: {dotenv_path}. Relying on system environment variables.") # For debugging

# Assuming these modules are in the app directory and Python path is set up correctly
try:
    from app.core.user_activity_monitor import (
        find_users_for_emailing,
        mark_user_processed,
        SCENARIO_COMPLETED_3_APPLICATIONS,
        SCENARIO_INACTIVE_1_OR_2_APPS,
        SCENARIO_NO_APPS_AFTER_SIGNUP
    )
    from app.services.email_service import send_transactional_email
except ImportError as e:
    logging.critical(f"Failed to import necessary modules: {e}. Ensure app structure is correct and PYTHONPATH includes 'app'.")
    # Define fallbacks if you want the script to attempt to run further for partial testing,
    # but this is generally not recommended for production schedulers.
    def find_users_for_emailing(): logging.error("find_users_for_emailing not imported"); return {}
    def mark_user_processed(uid, skey): logging.error("mark_user_processed not imported")
    def send_transactional_email(to, uname, skey, ctx): logging.error("send_transactional_email not imported"); return False
    SCENARIO_COMPLETED_3_APPLICATIONS = "completed_3_applications_fallback"
    SCENARIO_INACTIVE_1_OR_2_APPS = "inactive_1_or_2_apps_fallback"
    SCENARIO_NO_APPS_AFTER_SIGNUP = "no_apps_after_signup_fallback"


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for Redis (rate limit reset)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
FLASK_LIMITER_REDIS_PATTERN = os.environ.get('FLASK_LIMITER_REDIS_PATTERN', 'LIMITER/*')

scheduler = BlockingScheduler(timezone="UTC") # Explicitly set timezone

def reset_daily_rate_limits():
    """
    Connects to Redis and deletes keys associated with Flask-Limiter's daily limits.
    This function is intended to be run daily at midnight UTC.
    """
    logging.info("Starting daily rate limit reset job.")
    try:
        r = redis.from_url(REDIS_URL)
        r.ping() # Verify connection
        logging.info(f"Successfully connected to Redis at {REDIS_URL}.")

        # Use the configurable pattern for key discovery.
        # It's crucial to set FLASK_LIMITER_REDIS_PATTERN correctly
        # to avoid deleting unrelated keys.
        key_pattern = FLASK_LIMITER_REDIS_PATTERN
        logging.info(f"Using Redis key pattern: '{key_pattern}'")

        keys_to_delete = []
        # Scan for keys matching the pattern. Use scan_iter for large datasets.
        for key in r.scan_iter(match=key_pattern):
            keys_to_delete.append(key)
            logging.info(f"Found key for deletion: {key.decode('utf-8')}")

        if keys_to_delete:
            deleted_count = r.delete(*keys_to_delete)
            logging.info(f"Deleted {deleted_count} rate limit keys matching pattern '{key_pattern}'.")
        else:
            logging.info(f"No keys found matching pattern '{key_pattern}'. Nothing to delete.")

    except redis.exceptions.ConnectionError as e:
        logging.error(f"Could not connect to Redis: {e}")
    except Exception as e:
        logging.error(f"An error occurred during the rate limit reset process: {e}")

    logging.info("Daily rate limit reset job finished.")


def send_scheduled_emails():
    """
    Fetches users based on activity scenarios and sends them appropriate emails.
    Marks users as processed after successful email dispatch.
    """
    logging.info("Starting scheduled email sending process...")
    try:
        users_to_email_by_scenario = find_users_for_emailing()
        logging.info(f"users_to_email_by_scenario: {users_to_email_by_scenario}")  # Debugging line to see the structure

        if not users_to_email_by_scenario:
            logging.info("No users found for any email scenarios.")
            return

        for scenario_key, user_list in users_to_email_by_scenario.items():
            if not user_list:
                logging.info(f"No users found for scenario: {scenario_key}")
                continue

            logging.info(f"Processing {len(user_list)} users for scenario: {scenario_key}")
            for user_data in user_list:
                logging.info(f"Processing user data: {user_data}")  # Better logging
                user_id = user_data.get('user_id')
                email = user_data.get('email')
                user_name = user_data.get('user_name', '')

                if not user_id or not email:
                    logging.warning(f"Missing user_id or email for user data: {user_data}. Skipping.")
                    continue

                context = {}
                if scenario_key == SCENARIO_INACTIVE_1_OR_2_APPS:
                    context['application_count'] = user_data.get('application_count', 0)

                logging.info(f"Attempting to send email for scenario '{scenario_key}' to user {user_id} ({email}).")

                success = send_transactional_email(
                    to_email=email,
                    user_name=user_name,
                    scenario_key=scenario_key,
                    context=context
                )

                if success:
                    try:
                        mark_user_processed(user_id, scenario_key)
                        logging.info(f"Email sent successfully to user {user_id} for scenario '{scenario_key}', and user marked as processed.")
                    except Exception as e_mark:
                        logging.error(f"Successfully sent email to {user_id} for {scenario_key}, but FAILED to mark as processed: {e_mark}")
                else:
                    logging.error(f"Failed to send email to user {user_id} for scenario '{scenario_key}'. User not marked as processed.")

        logging.info("Scheduled email sending process completed.")

    except Exception as e:
        logging.error(f"An error occurred during the send_scheduled_emails job: {e}", exc_info=True)


if __name__ == "__main__":
    logging.info("Scheduler starting up...")

    # Schedule the rate limit reset job to run every day at midnight UTC
    # scheduler.add_job(reset_daily_rate_limits, 'cron', hour=0, minute=0, misfire_grace_time=None)
    # logging.info("Scheduled 'reset_daily_rate_limits' job for 00:00 UTC daily.")

    # Schedule the email sending job to run every Tuesday at 9:00 AM UTC
    # scheduler.add_job(send_scheduled_emails, 'cron', day_of_week='tue', hour=9, minute=0, misfire_grace_time=None)
    # logging.info("Scheduled 'send_scheduled_emails' job for Tuesdays at 09:00 UTC.")

    # logging.info("Scheduler started. Waiting for jobs to run... Press Ctrl+C to exit.")
     # Schedule the email sending job to run every 5 seconds
    scheduler.add_job(send_scheduled_emails, 'interval', seconds=5, misfire_grace_time=None)
    logging.info("Scheduled 'send_scheduled_emails' job for every 5 seconds.")

    logging.info("Scheduler started. Jobs will run every 5 seconds... Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped by user.")
    except Exception as e:
        logging.critical(f"Scheduler failed to start or crashed: {e}", exc_info=True)
