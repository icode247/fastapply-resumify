import requests
import datetime
import json
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for API endpoints
INTERNAL_USERS_API_URL = os.environ.get('INTERNAL_USERS_API_URL', "http://localhost:8001/internal/users")
INTERNAL_USER_APPLICATIONS_API_URL_TEMPLATE = os.environ.get('INTERNAL_USER_APPLICATIONS_API_URL_TEMPLATE', "http://localhost:8001/internal/users/{user_id}/applications")
NEW_USER_DAYS_THRESHOLD = int(os.environ.get('NEW_USER_DAYS_THRESHOLD', "7"))

# Scenario Keys
SCENARIO_COMPLETED_3_APPLICATIONS = "completed_3_applications"
SCENARIO_INACTIVE_1_OR_2_APPS = "inactive_1_or_2_apps"
SCENARIO_NO_APPS_AFTER_SIGNUP = "no_apps_after_signup"

# Data store for processed users
DATA_DIR = os.path.join(os.getcwd(), 'data')
PROCESSED_USERS_DB_PATH = os.path.join(DATA_DIR, 'processed_users.json')

def initialize_data_store():
    """Ensures the data directory and processed_users.json file exist."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            logging.info(f"Created data directory: {DATA_DIR}")
        except OSError as e:
            logging.error(f"Error creating data directory {DATA_DIR}: {e}")
            raise

    if not os.path.exists(PROCESSED_USERS_DB_PATH):
        try:
            with open(PROCESSED_USERS_DB_PATH, 'w') as f:
                json.dump({}, f)
            logging.info(f"Initialized processed users DB: {PROCESSED_USERS_DB_PATH}")
        except IOError as e:
            logging.error(f"Error initializing processed users DB {PROCESSED_USERS_DB_PATH}: {e}")
            raise

initialize_data_store()

def get_users_from_api():
    """Fetches all users from the internal users API."""
    logging.info(f"Fetching users from API: {INTERNAL_USERS_API_URL}")
    try:
        response = requests.get(INTERNAL_USERS_API_URL, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        users = response.json()
        logging.info(f"Successfully fetched {len(users)} users from API.")
        return users
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching users from API: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from users API: {e}")
        return []

def get_user_application_count_from_api(user_id):
    """Fetches the application count for a given user_id from the internal API."""
    url = INTERNAL_USER_APPLICATIONS_API_URL_TEMPLATE.format(user_id=user_id)
    logging.info(f"Fetching application count for user {user_id} from API: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Assuming the API returns a JSON like {'application_count': 3}
        data = response.json()
        count = data.get('application_count', 0)
        logging.info(f"Successfully fetched application count for user {user_id}: {count}")
        return count
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching application count for user {user_id}: {e}")
        return 0  # Return a default value in case of error
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from user applications API for user {user_id}: {e}")
        return 0

def load_processed_users():
    """Loads the processed users data from the JSON file."""
    try:
        with open(PROCESSED_USERS_DB_PATH, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        logging.warning(f"Processed users file not found: {PROCESSED_USERS_DB_PATH}. Returning empty dict.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {PROCESSED_USERS_DB_PATH}: {e}. Returning empty dict.")
        return {}

def save_processed_users(data):
    """Saves the processed users data to the JSON file."""
    try:
        with open(PROCESSED_USERS_DB_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Saved processed users data to {PROCESSED_USERS_DB_PATH}")
    except IOError as e:
        logging.error(f"Error saving processed users data to {PROCESSED_USERS_DB_PATH}: {e}")

def mark_user_processed(user_id, scenario_key):
    """Marks a user as processed for a given scenario."""
    processed_users = load_processed_users()
    if user_id not in processed_users:
        processed_users[user_id] = {}
    processed_users[user_id][scenario_key] = datetime.datetime.utcnow().isoformat()
    save_processed_users(processed_users)
    logging.info(f"Marked user {user_id} as processed for scenario '{scenario_key}'.")

def has_user_been_processed(user_id, scenario_key):
    """Checks if a user has been processed for a given scenario."""
    processed_users = load_processed_users()
    has_been_processed = user_id in processed_users and scenario_key in processed_users[user_id]
    if has_been_processed:
        logging.info(f"User {user_id} has already been processed for scenario '{scenario_key}'.")
    else:
        logging.info(f"User {user_id} has not yet been processed for scenario '{scenario_key}'.")
    return has_been_processed

def find_users_for_emailing():
    """
    Identifies users eligible for different email scenarios based on their activity.
    Returns a dictionary where keys are scenario keys and values are lists of user objects.
    """
    logging.info("Starting to find users for all emailing scenarios...")
    all_users_from_api = get_users_from_api()
    if not all_users_from_api:
        logging.warning("No users found from API. Exiting.")
        return {
            SCENARIO_COMPLETED_3_APPLICATIONS: [],
            SCENARIO_INACTIVE_1_OR_2_APPS: [],
            SCENARIO_NO_APPS_AFTER_SIGNUP: [],
        }

    # This list will store users who are "new" and have their app counts
    # It's an intermediate list before sorting into scenarios
    new_users_with_app_counts = []
    now_utc = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware datetime

    for user_api_data in all_users_from_api:
        user_id = user_api_data.get('user_id')
        signup_date_str = user_api_data.get('signup_date')

        if not user_id or not signup_date_str:
            logging.warning(f"User missing user_id or signup_date: {user_api_data.get('email', 'N/A')}. Skipping.")
            continue

        try:
            if signup_date_str.endswith('Z'):
                signup_date_str = signup_date_str[:-1] + '+00:00'
            signup_date = datetime.datetime.fromisoformat(signup_date_str)
            if signup_date.tzinfo is None: # Should ideally not happen if fromisoformat handles 'Z'
                signup_date = signup_date.replace(tzinfo=datetime.timezone.utc)
        except ValueError as e:
            logging.error(f"Error parsing signup_date '{signup_date_str}' for user {user_id}: {e}. Skipping.")
            continue

        user_api_data['signup_datetime'] = signup_date # Store datetime object for easier use

        # Filter for new users (within NEW_USER_DAYS_THRESHOLD)
        if (now_utc - signup_date).days <= NEW_USER_DAYS_THRESHOLD:
            logging.debug(f"User {user_id} (signed up on {signup_date_str}) is a new user.")
            application_count = get_user_application_count_from_api(user_id)
            logging.debug(f"User {user_id} has {application_count} applications.")

            # Prepare a user dictionary with essential info for scenarios
            user_data_for_scenarios = {
                'user_id': user_id,
                'email': user_api_data.get('email'),
                'signup_datetime': signup_date,
                'application_count': application_count
            }
            new_users_with_app_counts.append(user_data_for_scenarios)
        else:
            logging.debug(f"User {user_id} (signed up on {signup_date_str}) is not a new user (threshold: {NEW_USER_DAYS_THRESHOLD} days).")

    logging.info(f"Processed {len(all_users_from_api)} users from API, found {len(new_users_with_app_counts)} new users for scenario evaluation.")

    # Initialize results dictionary
    users_for_scenarios = {
        SCENARIO_COMPLETED_3_APPLICATIONS: [],
        SCENARIO_INACTIVE_1_OR_2_APPS: [],
        SCENARIO_NO_APPS_AFTER_SIGNUP: [],
    }

    one_day_ago = now_utc - datetime.timedelta(days=1)

    for user in new_users_with_app_counts:
        user_id = user['user_id']
        app_count = user['application_count']
        signup_dt = user['signup_datetime']

        # Scenario 1: Finished first 3 applications
        if app_count == 3:
            if not has_user_been_processed(user_id, SCENARIO_COMPLETED_3_APPLICATIONS):
                users_for_scenarios[SCENARIO_COMPLETED_3_APPLICATIONS].append(user)
                logging.info(f"User {user_id} eligible for '{SCENARIO_COMPLETED_3_APPLICATIONS}'. App count: {app_count}.")
            continue # User fits this scenario, no need to check others like "inactive"

        # Scenario 2: Applied to 1 or 2 and "stopped after a day"
        # User must be signed up for more than 1 day
        if app_count in [1, 2] and signup_dt < one_day_ago:
            if not has_user_been_processed(user_id, SCENARIO_INACTIVE_1_OR_2_APPS):
                # Also ensure they are not eligible for SCENARIO_COMPLETED_3_APPLICATIONS (implicitly handled by `continue` above)
                users_for_scenarios[SCENARIO_INACTIVE_1_OR_2_APPS].append(user)
                logging.info(f"User {user_id} eligible for '{SCENARIO_INACTIVE_1_OR_2_APPS}'. App count: {app_count}, Signup: {signup_dt}.")
            continue

        # Scenario 3: Signed up but has not applied (after a day)
        # User must be signed up for more than 1 day
        if app_count == 0 and signup_dt < one_day_ago:
            if not has_user_been_processed(user_id, SCENARIO_NO_APPS_AFTER_SIGNUP):
                users_for_scenarios[SCENARIO_NO_APPS_AFTER_SIGNUP].append(user)
                logging.info(f"User {user_id} eligible for '{SCENARIO_NO_APPS_AFTER_SIGNUP}'. App count: {app_count}, Signup: {signup_dt}.")

    for scenario, users_list in users_for_scenarios.items():
        logging.info(f"Found {len(users_list)} users for scenario '{scenario}'.")

    return users_for_scenarios


if __name__ == '__main__':
    logging.info("Running user activity monitor directly for testing...")

    # Ensure data store is ready (though it's called at module load)
    # initialize_data_store()

    # Example: Mocking API responses for local testing
    # You would need to set up a mock server or monkeypatch 'requests.get' for real testing without live APIs.
    # For now, this will call the live (or placeholder) APIs.

    identified_users_by_scenario = find_users_for_emailing()

    logging.info("\n--- Identified Users by Scenario ---")
    for scenario_key, user_list in identified_users_by_scenario.items():
        logging.info(f"\nScenario: {scenario_key}")
        if user_list:
            for user_data in user_list:
                logging.info(f"  User ID: {user_data['user_id']}, Email: {user_data.get('email', 'N/A')}, Apps: {user_data['application_count']}, Signup: {user_data['signup_datetime']}")
        else:
            logging.info("  No users identified for this scenario.")
    logging.info("\n--- End of Report ---")

    # Example of marking a user as processed (normally done after successful email)
    # if identified_users_by_scenario[SCENARIO_NO_APPS_AFTER_SIGNUP]:
    #     test_user_to_mark = identified_users_by_scenario[SCENARIO_NO_APPS_AFTER_SIGNUP][0]
    #     logging.info(f"Simulating marking user {test_user_to_mark['user_id']} for scenario {SCENARIO_NO_APPS_AFTER_SIGNUP}")
    #     mark_user_processed(test_user_to_mark['user_id'], SCENARIO_NO_APPS_AFTER_SIGNUP)
    #     # Verify it's marked
    #     has_user_been_processed(test_user_to_mark['user_id'], SCENARIO_NO_APPS_AFTER_SIGNUP)
    pass
