# Gemini and feedback testing

## 1. Configure local environment

Create a local `.env` file in the project root. Do not commit this file.

```dotenv
DJANGO_SECRET_KEY=replace-with-a-new-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

Generate a Django secret locally with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Never paste API keys or Django secrets into source files, commits, screenshots, or chat messages. If a key was ever committed, revoke it and create a replacement; deleting it from the latest version does not erase Git history.

## 2. Run local checks

Activate your virtual environment, install dependencies, and run:

```bash
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
```

The automated tests should not make live Gemini requests or consume API quota.

## 3. Test Gemini connectivity

After configuring a valid key in `.env`, run:

```bash
python manage.py check_gemini_api
```

This sends a small live request to the configured model and consumes a small amount of API quota. The command does not display the key.

## 4. Feedback and private conversations

Test these flows with separate student and staff accounts:

- Staff can publish announcements.
- Students see only announcements intended for their course.
- Students can access and reply only to their own conversation threads.
- Private-message forms include CSRF protection.
- Server-side authorization is checked before reading or saving messages.
- Invalid or empty message input is rejected.

## 5. Git workflow

Changes should be reviewed and tested on a feature branch before they are merged into `main`.
