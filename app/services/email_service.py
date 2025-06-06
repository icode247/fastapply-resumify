import os
import logging
import resend

# Attempt to import from app.email_templates
try:
    from app.utils.email_templates import (
        EMAIL_TEMPLATES,
        # YOUR_PLATFORM_NAME, # Removed this import
        SCENARIO_COMPLETED_3_APPLICATIONS,
        SCENARIO_INACTIVE_1_OR_2_APPS,
        SCENARIO_NO_APPS_AFTER_SIGNUP
    )
except ImportError:
    # Fallback for direct execution or if structure is different, though not ideal for production
    logging.warning("Could not import from app.email_templates. Using placeholder values if run directly.")
    EMAIL_TEMPLATES = {} # Should be populated if this is a real issue
    # YOUR_PLATFORM_NAME = "My Platform (Fallback)" # Removed
    SCENARIO_COMPLETED_3_APPLICATIONS = "completed_3_applications"
    SCENARIO_INACTIVE_1_OR_2_APPS = "inactive_1_or_2_apps"
    SCENARIO_NO_APPS_AFTER_SIGNUP = "no_apps_after_signup"


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration from Environment Variables ---
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL_ADDRESS = os.environ.get("SENDER_EMAIL_ADDRESS")
PLATFORM_NAME = os.environ.get("PLATFORM_NAME", "Our Platform") # Added
PLATFORM_LOGIN_URL = os.environ.get("PLATFORM_LOGIN_URL", "https://yourplatform.com/login")
PLATFORM_RESOURCES_URL = os.environ.get("PLATFORM_RESOURCES_URL", "https://yourplatform.com/resources") # Ensured it's here
TEST_RECIPIENT_EMAIL = os.environ.get("TEST_RECIPIENT_EMAIL") # For __main__ block

# Initialize Resend API key
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
else:
    logging.error("RESEND_API_KEY environment variable not set. Email sending will fail.")

if not SENDER_EMAIL_ADDRESS:
    logging.error("SENDER_EMAIL_ADDRESS environment variable not set. Email sending will fail.")

def send_transactional_email(to_email: str, user_name: str, scenario_key: str, context: dict = None) -> bool:
    """
    Sends a transactional email based on the scenario key.

    Args:
        to_email: The recipient's email address.
        user_name: The name of the user, for personalization.
        scenario_key: The key identifying the email template and scenario.
        context: A dictionary for additional placeholder values (e.g., application_count).

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if not RESEND_API_KEY or not SENDER_EMAIL_ADDRESS:
        logging.error("Resend API key or sender email address is not configured. Cannot send email.")
        return False

    if scenario_key not in EMAIL_TEMPLATES:
        logging.error(f"Scenario key '{scenario_key}' not found in EMAIL_TEMPLATES.")
        return False

    template = EMAIL_TEMPLATES[scenario_key]
    raw_subject = template["subject"]
    raw_body = template["body"]

    # Personalization
    display_user_name = user_name if user_name else "there"

    # Replace general placeholders
    personalized_subject = raw_subject.replace("[User Name/there]", display_user_name)
    # Note: Subject might not typically contain [PlatformName], but if it does, this will catch it.
    personalized_subject = personalized_subject.replace("[PlatformName]", PLATFORM_NAME)

    personalized_body = raw_body.replace("[User Name/there]", display_user_name)
    personalized_body = personalized_body.replace("[PlatformName]", PLATFORM_NAME)

    if context is None:
        context = {}

    # Scenario-specific placeholders
    if scenario_key == SCENARIO_INACTIVE_1_OR_2_APPS:
        app_count_str = str(context.get('application_count', 'some'))
        personalized_body = personalized_body.replace("[Number of Applications]", app_count_str)
        personalized_body = personalized_body.replace("[Link to resources/blog]", PLATFORM_RESOURCES_URL)

    elif scenario_key == SCENARIO_NO_APPS_AFTER_SIGNUP:
        personalized_body = personalized_body.replace("[Link to Login/Platform]", PLATFORM_LOGIN_URL)

    # Basic HTML wrapping if templates are plain text.
    # If templates are already HTML, this might not be necessary or could be adjusted.
    html_content = personalized_body.replace("\n", "<br>") # Simple conversion for now

    params = {
        "from": SENDER_EMAIL_ADDRESS,
        "to": [to_email],
        "subject": personalized_subject,
        "html": html_content, # Resend expects HTML content
    }

    try:
        logging.info(f"Attempting to send email for scenario '{scenario_key}' to {to_email}...")
        email_response = resend.Emails.send(params)
        logging.info(f"Email sent successfully to {to_email}. Message ID: {email_response.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email} for scenario '{scenario_key}'. Error: {e}")
        return False

if __name__ == "__main__":
    logging.info("Running email_service.py directly for testing...")

    if not RESEND_API_KEY:
        logging.error("Cannot run test: RESEND_API_KEY is not set.")
    elif not SENDER_EMAIL_ADDRESS:
        logging.error("Cannot run test: SENDER_EMAIL_ADDRESS is not set.")
    elif not TEST_RECIPIENT_EMAIL:
        logging.warning("TEST_RECIPIENT_EMAIL not set. Skipping test email sending.")
    else:
        logging.info(f"Attempting to send a test email to: {TEST_RECIPIENT_EMAIL}")

        # Test SCENARIO_NO_APPS_AFTER_SIGNUP
        test_scenario = SCENARIO_NO_APPS_AFTER_SIGNUP
        logging.info(f"Testing scenario: {test_scenario}")
        success1 = send_transactional_email(
            to_email=TEST_RECIPIENT_EMAIL,
            user_name="Test User",
            scenario_key=test_scenario,
            context={} # No extra context needed for this one
        )
        logging.info(f"Test email for '{test_scenario}' success: {success1}")

        # Test SCENARIO_INACTIVE_1_OR_2_APPS
        test_scenario_2 = SCENARIO_INACTIVE_1_OR_2_APPS
        logging.info(f"Testing scenario: {test_scenario_2}")
        success2 = send_transactional_email(
            to_email=TEST_RECIPIENT_EMAIL,
            user_name="Another Test User",
            scenario_key=test_scenario_2,
            context={"application_count": 2}
        )
        logging.info(f"Test email for '{test_scenario_2}' success: {success2}")

        # Test SCENARIO_COMPLETED_3_APPLICATIONS
        test_scenario_3 = SCENARIO_COMPLETED_3_APPLICATIONS
        logging.info(f"Testing scenario: {test_scenario_3}")
        success3 = send_transactional_email(
            to_email=TEST_RECIPIENT_EMAIL,
            user_name="Power User",
            scenario_key=test_scenario_3
        )
        logging.info(f"Test email for '{test_scenario_3}' success: {success3}")

    logging.info("Email service direct test run finished.")
