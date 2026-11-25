from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from counseling.services import _generate_text


class Command(BaseCommand):
    help = "Send a small live request using the configured Gemini API key."

    def handle(self, *args, **options):
        configured_key = getattr(settings, "GEMINI_API_KEY", "")
        if not isinstance(configured_key, str) or not configured_key.strip():
            raise CommandError(
                "No Gemini API key is configured. Add GEMINI_API_KEY to your local .env file."
            )

        self.stdout.write("Testing the configured Gemini connection...")

        try:
            answer = _generate_text(
                "Reply with exactly this text: GEMINI_CONNECTION_OK"
            )
            if not answer:
                raise RuntimeError("Gemini returned an empty response.")
        except Exception as exc:
            # Avoid printing exception details because SDK errors may contain request data.
            self.stderr.write(
                self.style.ERROR(
                    f"Gemini request failed ({type(exc).__name__})."
                )
            )
            raise CommandError(
                "The Gemini request failed. Check the API key, model name, "
                "API access, quota, and network connection. The key was not displayed."
            ) from None

        self.stdout.write(
            self.style.SUCCESS("Gemini API connection is working.")
        )
