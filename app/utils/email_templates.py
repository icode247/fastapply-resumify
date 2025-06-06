import textwrap

# These scenario keys would typically be imported from app.user_activity_monitor
# For simplicity here, we're defining them as strings, ensure they match.
SCENARIO_COMPLETED_3_APPLICATIONS = "completed_3_applications"
SCENARIO_INACTIVE_1_OR_2_APPS = "inactive_1_or_2_apps"
SCENARIO_NO_APPS_AFTER_SIGNUP = "no_apps_after_signup"

EMAIL_TEMPLATES = {
    SCENARIO_COMPLETED_3_APPLICATIONS: {
        "subject": "You're on a Roll! What's Next After 3 Applications?",
        "body": textwrap.dedent("""\
            Hi [User Name/there],

            Wow, you've already submitted 3 applications using our platform! That's fantastic momentum.

            Many of our users find that consistently applying increases their chances of landing interviews.
            If you're ready to take your job search to the next level, consider our yearly plan for unlimited applications and access to premium features.

            Keep up the great work!

            Best regards,
            The [PlatformName] Team
            """)
    },
    SCENARIO_INACTIVE_1_OR_2_APPS: {
        "subject": "Still Thinking About That Next Application?",
        "body": textwrap.dedent("""\
            Hi [User Name/there],

            We noticed you've started strong by submitting [Number of Applications] application(s)!

            Completing more applications can significantly boost your visibility to employers. Our platform makes it easy to tailor your resume and apply quickly.

            Need a little help or inspiration? Check out [Link to resources/blog] or simply log back in to continue.

            Ready to apply for more? Our yearly subscription gives you unlimited applications, or you can purchase additional credits.

            Best,
            The [PlatformName] Team
            """)
    },
    SCENARIO_NO_APPS_AFTER_SIGNUP: {
        "subject": "Ready to Land Your Dream Job? Start Your First Application!",
        "body": textwrap.dedent("""\
            Hi [User Name/there],

            Welcome again to [PlatformName]! We're excited to help you streamline your job application process.

            Getting started is easy. Just upload your resume, find a job you're interested in, and let us help you tailor your application. Your first 3 applications are on us!

            Don't let your dream job wait. Log in now and make your first application: [Link to Login/Platform]

            Good luck!

            Sincerely,
            The [PlatformName] Team
            """)
    }
}

if __name__ == '__main__':
    # Example of how to access and print a template
    print("--- Example Template ---")
    scenario = SCENARIO_INACTIVE_1_OR_2_APPS
    if scenario in EMAIL_TEMPLATES:
        subject = EMAIL_TEMPLATES[scenario]["subject"]
        body = EMAIL_TEMPLATES[scenario]["body"]

        # Example of replacing placeholders (simplified)
        body_personalized = body.replace("[User Name/there]", "Alex")
        body_personalized = body_personalized.replace("[Number of Applications]", "2")
        body_personalized = body_personalized.replace("[Link to resources/blog]", "http://example.com/blog")
        body_personalized = body_personalized.replace("[PlatformName]", "My Test Platform") # Example replacement

        print(f"Subject: {subject}")
        print("\nBody:\n")
        print(body_personalized)
    else:
        print(f"No template found for scenario: {scenario}")
