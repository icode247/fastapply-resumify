import unittest
from unittest import mock
import json
import datetime
import os
import shutil
import requests

# Ensure the app directory is in PYTHONPATH for imports if running tests directly
try:
    from app.core.user_activity_monitor import (
        get_users_from_api,
        get_user_applications_from_api,  # Fixed function name
        load_processed_users,
        save_processed_users,
        mark_user_processed,
        has_user_been_processed,
        find_users_for_emailing,
        initialize_data_store,
        SCENARIO_COMPLETED_3_APPLICATIONS,
        SCENARIO_INACTIVE_1_OR_2_APPS,
        SCENARIO_NO_APPS_AFTER_SIGNUP
    )
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from app.core.user_activity_monitor import (
        get_users_from_api,
        get_user_applications_from_api,  # Fixed function name
        load_processed_users,
        save_processed_users,
        mark_user_processed,
        has_user_been_processed,
        find_users_for_emailing,
        initialize_data_store,
        SCENARIO_COMPLETED_3_APPLICATIONS,
        SCENARIO_INACTIVE_1_OR_2_APPS,
        SCENARIO_NO_APPS_AFTER_SIGNUP
    )


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
            shutil.rmtree(self.TEST_DATA_DIR)
        os.makedirs(self.TEST_DATA_DIR)

        # Initialize the data store within the new patched directory
        initialize_data_store()

        # Patch environment variables - Updated URLs
        self.env_patcher_users_api = mock.patch.dict(os.environ, {
            "INTERNAL_USERS_API_URL": "http://localhost:3000/api/user/search",
            "INTERNAL_APPLICATIONS_API_URL_TEMPLATE": "http://localhost:3000/api/applications?userId={user_id}",
            "NEW_USER_DAYS_THRESHOLD": "7"
        })
        self.env_patcher_users_api.start()

        # Mock datetime
        self.mock_datetime = mock.patch('app.user_activity_monitor.datetime.datetime').start()
        self.fixed_now = datetime.datetime(2023, 1, 8, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.mock_datetime.now.return_value = self.fixed_now
        self.mock_datetime.utcnow.return_value = self.fixed_now
        self.mock_datetime.fromisoformat.side_effect = lambda s: datetime.datetime.fromisoformat(s)
        self.mock_datetime.side_effect = lambda *args, **kwargs: datetime.datetime(*args, **kwargs)

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.TEST_DATA_DIR):
            shutil.rmtree(self.TEST_DATA_DIR)
        self.env_patcher_users_api.stop()
        mock.patch.stopall()

    @mock.patch('app.user_activity_monitor.requests.post')  # Changed to POST
    def test_get_users_from_api_success(self, mock_post):
        """Test successful fetching of users from API."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        # Updated to match your API structure
        mock_users_data = [
            {
                "id": "user1", 
                "email": "a@b.com", 
                "firstName": "John",
                "lastName": "Doe",
                "createdAt": "2023-01-01T10:00:00Z"
            }
        ]
        mock_response.json.return_value = mock_users_data
        mock_post.return_value = mock_response

        users = get_users_from_api()
        self.assertEqual(users, mock_users_data)
        
        # Verify POST was called with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], 10)
        self.assertIn('json', call_args[1])

    @mock.patch('app.user_activity_monitor.requests.post')
    def test_get_users_from_api_error(self, mock_post):
        """Test API error when fetching users."""
        mock_post.side_effect = requests.exceptions.RequestException("API is down")
        users = get_users_from_api()
        self.assertEqual(users, [])

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_user_applications_success(self, mock_get):
        """Test successful fetching of user applications."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        # Updated to match your applications API structure
        mock_applications_data = [
            {
                "id": "app1",
                "userId": "user123",
                "appliedAt": {"seconds": 1642096042, "nanoseconds": 0},
                "title": "Test Job 1"
            },
            {
                "id": "app2", 
                "userId": "user123",
                "appliedAt": {"seconds": 1642182442, "nanoseconds": 0},
                "title": "Test Job 2"
            }
        ]
        mock_response.json.return_value = mock_applications_data
        mock_get.return_value = mock_response

        count, last_date = get_user_applications_from_api("user123")
        self.assertEqual(count, 2)
        self.assertIsNotNone(last_date)
        
        expected_url = "http://localhost:3000/api/applications?userId=user123"
        mock_get.assert_called_once_with(expected_url, timeout=10)

    @mock.patch('app.user_activity_monitor.requests.get')
    def test_get_user_applications_error(self, mock_get):
        """Test API error when fetching user applications."""
        mock_get.side_effect = requests.exceptions.RequestException("API is down")
        count, last_date = get_user_applications_from_api("user123")
        self.assertEqual(count, 0)
        self.assertIsNone(last_date)

    def test_load_processed_users(self):
        """Test loading processed users from file."""
        # Test loading from initialized empty file
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
        self.assertEqual(data, {})

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

        mark_user_processed(user_id, scenario)
        self.assertTrue(has_user_been_processed(user_id, scenario))

        processed_data = load_processed_users()
        self.assertIn(user_id, processed_data)
        self.assertIn(scenario, processed_data[user_id])
        self.assertIsNotNone(processed_data[user_id][scenario])

    @mock.patch('app.user_activity_monitor.get_user_applications_from_api')  # Fixed function name
    @mock.patch('app.user_activity_monitor.get_users_from_api')
    def test_find_users_for_emailing_scenarios(self, mock_get_users, mock_get_applications):
        """Test the main logic of find_users_for_emailing for various scenarios."""

        # --- SCENARIO: New user, 0 apps, >1 day old ---
        mock_get_users.return_value = [
            {
                "id": "user1",  # Changed from user_id to id
                "email": "user1@test.com", 
                "firstName": "John",
                "lastName": "Doe",
                "createdAt": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"  # Changed from signup_date to createdAt
            }
        ]
        mock_get_applications.return_value = (0, None)  # (count, last_date)
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 1)
        self.assertEqual(results[SCENARIO_NO_APPS_AFTER_SIGNUP][0]['user_id'], "user1")
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)

        # --- SCENARIO: New user, 1 app, >1 day old ---
        save_processed_users({})  # Reset processed users
        mock_get_users.return_value = [
            {
                "id": "user2", 
                "email": "user2@test.com",
                "firstName": "Jane", 
                "lastName": "Smith",
                "createdAt": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"
            }
        ]
        # Last application was 2 days ago, so user is inactive
        last_app_date = self.fixed_now - datetime.timedelta(days=2)
        mock_get_applications.return_value = (1, last_app_date)
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 1)
        self.assertEqual(results[SCENARIO_INACTIVE_1_OR_2_APPS][0]['user_id'], "user2")
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)

        # --- SCENARIO: New user, 3 apps ---
        save_processed_users({})
        mock_get_users.return_value = [
            {
                "id": "user3", 
                "email": "user3@test.com",
                "firstName": "Bob",
                "lastName": "Wilson", 
                "createdAt": (self.fixed_now - datetime.timedelta(days=1)).isoformat() + "Z"
            }
        ]
        last_app_date = self.fixed_now - datetime.timedelta(hours=1)
        mock_get_applications.return_value = (3, last_app_date)
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 1)
        self.assertEqual(results[SCENARIO_COMPLETED_3_APPLICATIONS][0]['user_id'], "user3")
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)

        # --- SCENARIO: User signed up too long ago (older than NEW_USER_DAYS_THRESHOLD) ---
        save_processed_users({})
        mock_get_users.return_value = [
            {
                "id": "user4", 
                "email": "user4@test.com",
                "firstName": "Alice",
                "lastName": "Brown",
                "createdAt": (self.fixed_now - datetime.timedelta(days=10)).isoformat() + "Z"
            }
        ]
        mock_get_applications.return_value = (1, None)
        results = find_users_for_emailing()
        # Should be empty because user is filtered out at API level (too old)
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)

        # --- SCENARIO: User already processed for a matching scenario ---
        save_processed_users({})
        mark_user_processed("user1", SCENARIO_NO_APPS_AFTER_SIGNUP)
        mock_get_users.return_value = [
            {
                "id": "user1", 
                "email": "user1@test.com",
                "firstName": "John",
                "lastName": "Doe",
                "createdAt": (self.fixed_now - datetime.timedelta(days=2)).isoformat() + "Z"
            }
        ]
        mock_get_applications.return_value = (0, None)
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)

        # --- SCENARIO: User signed up recently, 0 apps, but LESS than 1 day old ---
        save_processed_users({})
        mock_get_users.return_value = [
            {
                "id": "user5", 
                "email": "user5@test.com",
                "firstName": "Charlie",
                "lastName": "Davis", 
                "createdAt": (self.fixed_now - datetime.timedelta(hours=12)).isoformat() + "Z"
            }
        ]
        mock_get_applications.return_value = (0, None)
        results = find_users_for_emailing()
        self.assertEqual(len(results[SCENARIO_NO_APPS_AFTER_SIGNUP]), 0)
        self.assertEqual(len(results[SCENARIO_INACTIVE_1_OR_2_APPS]), 0)
        self.assertEqual(len(results[SCENARIO_COMPLETED_3_APPLICATIONS]), 0)


if __name__ == '__main__':
    unittest.main()