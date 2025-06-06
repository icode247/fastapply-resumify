import requests
import datetime
import json
import os
import logging

# Configure basic logging with more detailed format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for API endpoints - CORRECTED URLS
API_HOST = os.environ.get('API_HOST', 'http://localhost:3000')
INTERNAL_USERS_API_URL = API_HOST + '/api/users/search'
INTERNAL_APPLICATIONS_API_URL_TEMPLATE = API_HOST + '/api/applications/user/{user_id}'
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
    """Fetches users from the internal users API using POST request."""
    logging.info(f"🔍 DEBUG: Fetching users from API: {INTERNAL_USERS_API_URL}")
    
    # POST body for user search - filtering by createdAt for new users
    request_body = {
        "collection": "users",
        "filters": [
            {
                "field": "createdAt", 
                "operator": ">=", 
                "value": (datetime.datetime.utcnow() - datetime.timedelta(days=NEW_USER_DAYS_THRESHOLD)).isoformat() + "Z"
            }
        ],
        "fields": ["id", "email", "firstName", "lastName", "createdAt", "applicationsUsed", "onboarded"]
    }
    
    logging.info(f"🔍 DEBUG: Request body being sent: {json.dumps(request_body, indent=2)}")
    
    try:
        response = requests.post(INTERNAL_USERS_API_URL, json=request_body, timeout=10)
        logging.info(f"🔍 DEBUG: Response status code: {response.status_code}")
        logging.info(f"🔍 DEBUG: Response headers: {dict(response.headers)}")
        
        response.raise_for_status()
        
        # Log the raw response text
        raw_response = response.text
        logging.info(f"🔍 DEBUG: Raw response text (first 1000 chars): {raw_response[:1000]}")
        logging.info(f"🔍 DEBUG: Raw response text (full length): {len(raw_response)} characters")
        
        # Try to parse JSON
        try:
            users = response.json()
            logging.info(f"🔍 DEBUG: JSON parsing successful!")
            logging.info(f"🔍 DEBUG: Parsed response type: {type(users)}")
            logging.info(f"🔍 DEBUG: Parsed response: {repr(users)}")
            
            if hasattr(users, '__len__'):
                logging.info(f"🔍 DEBUG: Response length: {len(users)}")
            
            if isinstance(users, list):
                logging.info(f"🔍 DEBUG: Response is a list with {len(users)} items")
                for i, item in enumerate(users[:3]):  # Show first 3 items
                    logging.info(f"🔍 DEBUG: Item {i} - Type: {type(item)}, Content: {repr(item)}")
            elif isinstance(users, dict):
                logging.info(f"🔍 DEBUG: Response is a dict with keys: {list(users.keys())}")
                logging.info(f"🔍 DEBUG: Dict content: {users}")
            else:
                logging.info(f"🔍 DEBUG: Response is unexpected type: {type(users)}")
                
        except json.JSONDecodeError as e:
            logging.error(f"🔍 DEBUG: JSON decode error: {e}")
            logging.error(f"🔍 DEBUG: Raw response that failed to parse: {raw_response}")
            return []
        
        logging.info(f"✅ Successfully fetched data from API. Type: {type(users)}, Length: {len(users) if hasattr(users, '__len__') else 'N/A'}")
        return users
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error fetching users from API: {e}")
        return []

def get_user_applications_from_api(user_id):
    """Fetches applications for a given user_id and returns count and last application date."""
    url = INTERNAL_APPLICATIONS_API_URL_TEMPLATE.format(user_id=user_id)
    logging.info(f"🔍 DEBUG: Fetching applications for user {user_id} from API: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        logging.info(f"🔍 DEBUG: Applications API response status: {response.status_code}")
        
        response.raise_for_status()
        
        # Log raw response for applications
        raw_response = response.text
        logging.info(f"🔍 DEBUG: Applications raw response (first 500 chars): {raw_response[:500]}")
        
        applications = response.json()
        logging.info(f"🔍 DEBUG: Applications response type: {type(applications)}")
        logging.info(f"🔍 DEBUG: Applications response: {repr(applications)}")
        
        application_count = len(applications) if isinstance(applications, list) else 0
        last_application_date = None
        
        if applications and isinstance(applications, list):
            # Find the most recent application
            try:
                latest_app = max(applications, key=lambda app: app['appliedAt']['seconds'])
                # Convert timestamp to datetime
                timestamp = latest_app['appliedAt']['seconds']
                last_application_date = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            except (KeyError, TypeError, ValueError) as e:
                logging.error(f"🔍 DEBUG: Error parsing application dates: {e}")
        
        logging.info(f"✅ User {user_id} has {application_count} applications. Last application: {last_application_date}")
        return application_count, last_application_date
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error fetching applications for user {user_id}: {e}")
        return 0, None
    except json.JSONDecodeError as e:
        logging.error(f"❌ Error decoding JSON response from applications API for user {user_id}: {e}")
        return 0, None

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
    logging.info("🚀 Starting to find users for all emailing scenarios...")
    
    all_users_from_api = get_users_from_api()
    
    logging.info(f"🔍 DEBUG: API returned data type: {type(all_users_from_api)}")
    logging.info(f"🔍 DEBUG: API returned data: {repr(all_users_from_api)}")
    
    if not all_users_from_api:
        logging.warning("❌ No users found from API. Exiting.")
        return {
            SCENARIO_COMPLETED_3_APPLICATIONS: [],
            SCENARIO_INACTIVE_1_OR_2_APPS: [],
            SCENARIO_NO_APPS_AFTER_SIGNUP: [],
        }

    # Handle different response structures
    users_list = []
    if isinstance(all_users_from_api, list):
        users_list = all_users_from_api
        logging.info(f"✅ API returned a list with {len(users_list)} items")
    elif isinstance(all_users_from_api, dict):
        # Check if it's a wrapped response
        if 'users' in all_users_from_api:
            users_list = all_users_from_api['users']
            logging.info(f"✅ API returned dict with 'users' key containing {len(users_list)} items")
        elif 'data' in all_users_from_api:
            users_list = all_users_from_api['data']
            logging.info(f"✅ API returned dict with 'data' key containing {len(users_list)} items")
        else:
            logging.error(f"❌ API returned dict but no recognized data key. Keys: {list(all_users_from_api.keys())}")
            return {
                SCENARIO_COMPLETED_3_APPLICATIONS: [],
                SCENARIO_INACTIVE_1_OR_2_APPS: [],
                SCENARIO_NO_APPS_AFTER_SIGNUP: [],
            }
    else:
        logging.error(f"❌ API returned unexpected type: {type(all_users_from_api)}")
        return {
            SCENARIO_COMPLETED_3_APPLICATIONS: [],
            SCENARIO_INACTIVE_1_OR_2_APPS: [],
            SCENARIO_NO_APPS_AFTER_SIGNUP: [],
        }

    logging.info(f"🔍 DEBUG: Processing {len(users_list)} users from API")

    # This list will store users who are "new" and have their app counts
    new_users_with_app_data = []
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    for i, user_api_data in enumerate(users_list):
        logging.info(f"🔍 DEBUG: Processing user {i+1}/{len(users_list)}")
        logging.info(f"🔍 DEBUG: User data type: {type(user_api_data)}")
        logging.info(f"🔍 DEBUG: User data content: {repr(user_api_data)}")
        
        # Handle string users (if that's what we're getting)
        if isinstance(user_api_data, str):
            logging.warning(f"⚠️  User data is a string: {user_api_data}. Attempting to parse as JSON.")
            try:
                user_api_data = json.loads(user_api_data)
                logging.info(f"✅ Successfully parsed string as JSON: {user_api_data}")
            except json.JSONDecodeError:
                logging.error(f"❌ Could not parse user data as JSON: {user_api_data}. Skipping.")
                continue
        
        # Ensure we have a dictionary now
        if not isinstance(user_api_data, dict):
            logging.error(f"❌ User data is not a dict after processing. Type: {type(user_api_data)}, Content: {user_api_data}. Skipping.")
            continue
        
        # Use correct field names from your API
        user_id = user_api_data.get('id')
        created_at_str = user_api_data.get('createdAt')
        email = user_api_data.get('email')
        first_name = user_api_data.get('firstName', '')
        last_name = user_api_data.get('lastName', '')
        
        logging.info(f"🔍 DEBUG: Extracted data - ID: {user_id}, Email: {email}, CreatedAt: {created_at_str}")
        
        if not user_id or not created_at_str:
            logging.warning(f"⚠️  User missing id or createdAt: {email or 'N/A'}. Available keys: {list(user_api_data.keys())}. Skipping.")
            continue

        try:
            # Parse the createdAt timestamp
            if created_at_str.endswith('Z'):
                signup_date = datetime.datetime.fromisoformat(created_at_str[:-1] + '+00:00')
            else:
                signup_date = datetime.datetime.fromisoformat(created_at_str)
            
            if signup_date.tzinfo is None:
                signup_date = signup_date.replace(tzinfo=datetime.timezone.utc)
                
            logging.info(f"✅ Parsed signup date: {signup_date}")
        except ValueError as e:
            logging.error(f"❌ Error parsing createdAt '{created_at_str}' for user {user_id}: {e}. Skipping.")
            continue

        # Filter for recent users (within NEW_USER_DAYS_THRESHOLD)
        days_since_signup = (now_utc - signup_date).days
        logging.info(f"🔍 DEBUG: User {user_id} signed up {days_since_signup} days ago (threshold: {NEW_USER_DAYS_THRESHOLD})")
        
        if days_since_signup <= NEW_USER_DAYS_THRESHOLD:
            logging.info(f"✅ User {user_id} is a recent user (within threshold)")
            
            # Get application count and last application date
            application_count, last_application_date = get_user_applications_from_api(user_id)
            logging.info(f"✅ User {user_id} has {application_count} applications.")

            # Prepare user data for scenarios
            user_data_for_scenarios = {
                'user_id': user_id,
                'email': email,
                'user_name': f"{first_name} {last_name}".strip(),
                'signup_datetime': signup_date,
                'application_count': application_count,
                'last_application_date': last_application_date
            }
            new_users_with_app_data.append(user_data_for_scenarios)
            logging.info(f"✅ Added user {user_id} to processing list")
        else:
            logging.info(f"⏭️  User {user_id} is not recent (threshold: {NEW_USER_DAYS_THRESHOLD} days).")

    logging.info(f"📊 Processed {len(users_list)} users from API, found {len(new_users_with_app_data)} recent users for scenario evaluation.")

    # Initialize results dictionary
    users_for_scenarios = {
        SCENARIO_COMPLETED_3_APPLICATIONS: [],
        SCENARIO_INACTIVE_1_OR_2_APPS: [],
        SCENARIO_NO_APPS_AFTER_SIGNUP: [],
    }

    one_day_ago = now_utc - datetime.timedelta(days=1)

    for user in new_users_with_app_data:
        user_id = user['user_id']
        app_count = user['application_count']
        signup_dt = user['signup_datetime']
        last_app_date = user['last_application_date']

        logging.info(f"🔍 DEBUG: Evaluating scenarios for user {user_id} - Apps: {app_count}, Signup: {signup_dt}, Last app: {last_app_date}")

        # Scenario 1: Completed 3 applications
        if app_count >= 3:
            logging.info(f"🎯 User {user_id} has {app_count} apps (>=3), checking if already processed for scenario 1")
            if not has_user_been_processed(user_id, SCENARIO_COMPLETED_3_APPLICATIONS):
                users_for_scenarios[SCENARIO_COMPLETED_3_APPLICATIONS].append(user)
                logging.info(f"✅ User {user_id} eligible for '{SCENARIO_COMPLETED_3_APPLICATIONS}'. App count: {app_count}.")
            continue

        # Scenario 2: Applied to 1 or 2 and inactive
        if app_count in [1, 2]:
            is_inactive = False
            if last_app_date and (now_utc - last_app_date).days >= 1:
                is_inactive = True
                logging.info(f"🎯 User {user_id} inactive - last app {(now_utc - last_app_date).days} days ago")
            elif not last_app_date and signup_dt < one_day_ago:
                is_inactive = True
                logging.info(f"🎯 User {user_id} inactive - no apps and signed up {(now_utc - signup_dt).days} days ago")
            
            if is_inactive and not has_user_been_processed(user_id, SCENARIO_INACTIVE_1_OR_2_APPS):
                users_for_scenarios[SCENARIO_INACTIVE_1_OR_2_APPS].append(user)
                logging.info(f"✅ User {user_id} eligible for '{SCENARIO_INACTIVE_1_OR_2_APPS}'. App count: {app_count}, Last app: {last_app_date}.")
            continue

        # Scenario 3: No applications after signup
        if app_count == 0 and signup_dt < one_day_ago:
            logging.info(f"🎯 User {user_id} has 0 apps and signed up {(now_utc - signup_dt).days} days ago")
            if not has_user_been_processed(user_id, SCENARIO_NO_APPS_AFTER_SIGNUP):
                users_for_scenarios[SCENARIO_NO_APPS_AFTER_SIGNUP].append(user)
                logging.info(f"✅ User {user_id} eligible for '{SCENARIO_NO_APPS_AFTER_SIGNUP}'. App count: {app_count}, Signup: {signup_dt}.")

    for scenario, users_list in users_for_scenarios.items():
        logging.info(f"📈 Found {len(users_list)} users for scenario '{scenario}'.")

    return users_for_scenarios


if __name__ == '__main__':
    logging.info("🚀 Running user activity monitor...")
    
    identified_users_by_scenario = find_users_for_emailing()

    logging.info("\n📊 === FINAL RESULTS ===")
    for scenario_key, user_list in identified_users_by_scenario.items():
        logging.info(f"\n🎯 Scenario: {scenario_key}")
        if user_list:
            for user_data in user_list:
                logging.info(f"  👤 User ID: {user_data['user_id']}, Email: {user_data.get('email', 'N/A')}, Apps: {user_data['application_count']}, Last App: {user_data.get('last_application_date', 'N/A')}")
        else:
            logging.info("  ❌ No users identified for this scenario.")
    logging.info("\n📊 === END OF REPORT ===")