# Feedback and Gemini verification

## Run the Django test suite

Activate your virtual environment, install the dependencies, and run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test

You can also run these checks manually from GitHub: open **Actions → Django checks → Run workflow** on the feature branch.
```

The automated tests use an empty Gemini setting so they do not spend API quota or make external Gemini requests.

## Test the currently configured Gemini API key

To verify the key configured in your local Django settings, run:

```bash
python manage.py check_gemini_api
```

This command sends a small live request to Gemini. A successful result confirms that the configured key can currently reach the selected model. A failure may indicate an invalid/restricted key, unavailable model, disabled API access, network trouble, or exhausted quota.

The command does not print or change the key. It does consume a small amount of API quota.

## Feedback and private conversations

- Teachers and admins can post course announcements and open student conversation threads.
- Students can view announcements matching their course and reply only in their own threads.
- Both private-message forms include CSRF protection.
- The server checks that the current user belongs to the conversation before showing or saving messages.
- Message and announcement input is validated before saving.

## Git workflow

All changes for this work are on `fix/feedback-private-chat-csrf-api`. Review the draft pull request before merging it into `main`.
