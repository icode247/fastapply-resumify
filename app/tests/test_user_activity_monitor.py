import unittest
from unittest import mock
import json
import datetime
import os
import shutil

# Ensure the app directory is in PYTHONPATH for imports if running tests directly
# This might require adjustments based on how tests are run (e.g., from project root)
# For now, assuming 'app' is discoverable or tests are run with 'python -m unittest discover' from root.
try:
    from app.user_activity_monitor import (
        get_users_from_api,
        get_user_application_count_from_api,
        load_processed_users,
        save_processed_users,
        mark_user_processed,
        has_user_been_processed,
        find_users_for_emailing,
        initialize_data_store, # To re-initialize with patched paths
        SCENARIO_COMPLETED_3_APPLICATIONS,
        SCENARIO_INACTIVE_1_OR_2_APPS,
        SCENARIO_NO_APPS_AFTER_SIGNUP
    )
except ImportError:
    # This block helps if running the test file directly and paths are tricky.
    # It's better to configure PYTHONPATH or use a test runner that handles this.
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from app.user_activity_monitor import (
        get_users_from_api, get_user_application_count_from_api, load_processed_users,
        save_processed_users, mark_user_processed, has_user_been_processed,
        find_users_for_emailing, initialize_data_store,
        SCENARIO_COMPLETED_3_APPLICATIONS, SCENARIO_INACTIVE_1_OR_2_APPS, SCENARIO_NO_APPS_AFTER_SIGNUP
    )

# Store original paths from the module to restore them later if needed,
# though patching should ideally handle cleanup.
ORIGINAL_DATA_DIR = os.environ.get("UAM_DATA_DIR_ORIG", "app.user_activity_monitor.DATA_DIR") # Placeholder if not set
ORIGINAL_DB_PATH = os.environ.get("UAM_DB_PATH_ORIG", "app.user_activity_monitor.PROCESSED_USERS_DB_PATH")


class TestUserActivityMonitor(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.TEST_DATA_DIR = os.path.join(os.getcwd(), "test_data_uam_temp")
        self.TEST_PROCESSED_USERS_DB_PATH = os.path.join(self.TEST_DATA_DIR, 'processed_users.json')

        # Patch module-level variables in user_activity_monitor
        self.data_dir_patcher = mock.patch('app.user_activity_monitor.DATA_DIR', self.TEST_DATA_DIR)
        self.db_path_patcher = mock.patch('app.user_activity_monitor.PROCESSED_USERS_DB_PATH', self.TEST_PROCESSED_USERS_DB_PATH)

        self.mock_data_dir = self.data_dir_patcher.start()
        self.mock_db_path = self.db_path_patcher.start()

        # Ensure the test data directory exists
        if os.path.exists(self.TEST_DATA_DIR):
            shutil.rmtree(self.TEST_DATA_DIR) # Clean up from previous failed test if any
        os.makedirs(self.TEST_DATA_DIR)

        # Initialize the data store within the new patched directory
        initialize_data_store()

        # Patch environment variables
        self.env_patcher_users_api = mock.patch.dict(os.environ, {
            "INTERNAL_USERS_API_URL": "http://mockapi.test/internal/users",
            "INTERNAL_USER_APPLICATIONS_API_URL_TEMPLATE": "http://mockapi.test/internal/users/{user_id}/applications",
            "NEW_USER_DAYS_THRESHOLD": "7"
        })
        self.env_patcher_users_api.start()

        # Mock datetime
        self.mock_datetime = mock.patch('app.user_activity_monitor.datetime.datetime').start()
        self.fixed_now = datetime.datetime(2023, 1, 8, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.mock_datetime.now.return_value = self.fixed_now
        self.mock_datetime.utcnow.return_value = self.fixed_now # if utcnow is used
        self.mock_datetime.fromisoformat.side_effect = lambda s: datetime.datetime.fromisoformat(s)
        self.mock_datetime.side_effect = lambda *args, **kwargs: datetime.datetime(*args, **kwargs)


    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.TEST_DATA_DIR)
        self.env_patcher_users_api.stop()
        mock.patch.stopall() # Stops all patches started with start()

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_users_from_api_success(self, mock_get):
        """Test successful fetching of users from API."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_users_data = [{"user_id": "1", "email": "a@b.com", "signup_date": "2023-01-01T10:00:00Z"}]
        mock_response.json.return_value = mock_users_data
        mock_get.return_value = mock_response

        users = get_users_from_api()
        self.assertEqual(users, mock_users_data)
        mock_get.assert_called_once_with("http://mockapi.test/internal/users", timeout=10)

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_users_from_api_error(self, mock_get):
        """Test API error when fetching users."""
        mock_get.side_effect = requests.exceptions.RequestException("API is down")
        users = get_users_from_api()
        self.assertEqual(users, [])

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_user_application_count_success(self, mock_get):
        """Test successful fetching of user application count."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"application_count": 5}
        mock_get.return_value = mock_response

        count = get_user_application_count_from_api("user123")
        self.assertEqual(count, 5)
        expected_url = "http://mockapi.test/internal/users/user123/applications"
        mock_get.assert_called_once_with(expected_url, timeout=10)

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_user_application_count_error(self, mock_get):
        """Test API error when fetching user application count."""
        mock_get.side_effect = requests.exceptions.RequestException("API is down")
        count = get_user_application_count_from_api("user123")
        self.assertEqual(count, 0)

    def test_load_processed_users(self):
        """Test loading processed users from file."""
        # Test loading from non-existent file (should be handled by initialize_data_store)
        data = load_processed_users()
        self.assertEqual(data, {})

        # Test loading empty JSON
        save_processed_users({})
        data = load_processed_users()
        self.assertEqual(data, {})

        # Test loading corrupt JSON
        with open(self.TEST_PROCESSED_USERS_DB_PATH, 'w') as f:
            f.write("this is not json")
        data = load_processed_users()
        self.assertEqual(data, {}) # Should return empty dict on JSONDecodeError

    def test_save_and_load_processed_users(self):
        """Test saving and then loading processed users."""
        test_data = {"user1": {"scenarioA": "2023-01-01T00:00:00"}}
        save_processed_users(test_data)
        loaded_data = load_processed_users()
        self.assertEqual(loaded_data, test_data)

    def test_mark_and_has_user_been_processed(self):
        """Test marking a user and checking if processed."""
        user_id = "user_test_mark"
        scenario = "test_scenario_mark"

        self.assertFalse(has_user_been_processed(user_id, scenario))

        # Mock datetime.utcnow for mark_user_processed if it's used there directly
        # However, our find_users_for_emailing mock setup already mocks datetime.datetime.now
        # which is what mark_user_processed uses if it's datetime.datetime.utcnow()
        # Let's assume the mock_datetime.utcnow (aliased to self.fixed_now) covers it.

        mark_user_processed(user_id, scenario)
        self.assertTrue(has_user_been_processed(user_id, scenario))

        processed_data = load_processed_users()
        self.assertIn(user_id, processed_data)
        self.assertIn(scenario, processed_data[user_id])
        # Check if timestamp is close to self.fixed_now.isoformat()
        # This part might be tricky due to how datetime is mocked or used.
        # For now, presence is key.
        self.assertIsNotNone(processed_data[user_id][scenario])


    @mock.patch('app.user_activity_monitor.get_user_application_count_from_api')
    @mock.patch('app.user_activity_monitor.get_users_from_api')
    def test_find_users_for_emailing_scenarios(self, mock_get_users, mock_get_app_count):
        """Test the main logic of find_users_for_emailing for various scenarios."""

        # --- SCENARIO: New user, 0 apps, >1 day old ---
        mock_get_users.return_value = [
            {"user_id": "user1", "email": "user1@test.com", "signup_date": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 0
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 1)
        self.assertEqual(results[SCENARIO_NO_APPS_AFTER_SIGNUP][0]['user_id'], "user1")
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)

        # --- SCENARIO: New user, 1 app, >1 day old ---
        save_processed_users({}) # Reset processed users
        mock_get_users.return_value = [
            {"user_id": "user2", "email": "user2@test.com", "signup_date": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 1
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 1)
        self.assertEqual(results[SCENARIO_INACTIVE_1_OR_2_APPS][0]['user_id'], "user2")
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)

        # --- SCENARIO: New user, 3 apps (any age within NEW_USER_DAYS_THRESHOLD) ---
        save_processed_users({})
        mock_get_users.return_value = [
            {"user_id": "user3", "email": "user3@test.com", "signup_date": (self.fixed_now - datetime.timedelta(days=1)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 3
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 1)
        self.assertEqual(results[SCENARIO_COMPLETED_3_APPLICATIONS][0]['user_id'], "user3")
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)

        # --- SCENARIO: User signed up too long ago (older than NEW_USER_DAYS_THRESHOLD) ---
        save_processed_users({})
        mock_get_users.return_value = [
            {"user_id": "user4", "email": "user4@test.com", "signup_date": (self.fixed_now - datetime.timedelta(days=10)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 1 # App count doesn't matter if too old
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)

        # --- SCENARIO: User already processed for a matching scenario ---
        save_processed_users({})
        mark_user_processed("user1", SCENARIO_NO_APPS_AFTER_SIGNUP) # Pre-mark user1
        mock_get_users.return_value = [
            {"user_id": "user1", "email": "user1@test.com", "signup_date": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 0
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0) # Should be empty because user1 is processed

        # --- SCENARIO: User signed up recently, 0 apps, but LESS than 1 day old ---
        # (Should NOT be in SCENARIO_NO_APPS_AFTER_SIGNUP which requires >1 day)
        save_processed_users({})
        mock_get_users.return_value = [
            {"user_id": "user5", "email": "user5@test.com", "signup_date": (self.fixed_now - datetime.timedelta(hours=12)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 0
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)

        # --- SCENARIO: User with 2 apps, but LESS than 1 day old ---
        # (Should NOT be in SCENARIO_INACTIVE_1_OR_2_APPS)
        save_processed_users({})
        mock_get_users.return_value = [
            {"user_id": "user6", "email": "user6@test.com", "signup_date": (self.fixed_now - datetime.timedelta(hours=12)).isoformat() + "Z"}
        ]
        mock_get_app_count.return_value = 2
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)


if __name__ == '__main__':
    # This allows running the tests directly from this file
    # However, it's often better to use 'python -m unittest discover' from the project root

    # A bit of setup to help imports if run directly, similar to try-except at top
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Need to import requests for the side_effect in API error tests
    import requests

    unittest.main()

# Placeholder for requests.exceptions.RequestException if requests is not available
# during initial linting or before tests fully run with proper environment.
class requests:
    class exceptions:
        class RequestException(Exception):
            pass
