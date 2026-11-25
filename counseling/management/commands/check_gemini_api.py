from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from counseling.services import _build_model, _extract_text


class Command(BaseCommand):
    help = "Send a small live request using the currently configured Gemini API key."

    def handle(self, *args, **options):
        configured_key = getattr(settings, "GEMINI_API_KEY", "")
        if not isinstance(configured_key, str) or not configured_key.strip():
            raise CommandError(
                "No Gemini API key is configured in Django settings. "
                "The key itself is never displayed by this command."
            )

        self.stdout.write("Testing the configured Gemini connection...")
        try:
            model = _build_model()
            if model is None:
                raise RuntimeError("Gemini model could not be initialized.")

            response = model.generate_content(
                "Reply with exactly this text: GEMINI_CONNECTION_OK"
            )
            answer = _extract_text(response)
            if not answer:
                raise RuntimeError("Gemini returned no readable text.")
        except Exception as exc:
            # Do not print the exception message: SDK errors can contain request details.
            error_name = exc.__class__.__name__
            self.stderr.write(self.style.ERROR(f"Gemini request failed ({error_name})."))
            raise CommandError(
                "The live Gemini request did not succeed. Check API-key validity, "
                "Gemini API access, model availability, and quota in Google AI Studio. "
                "This command did not display or modify your key."
            ) from None

        self.stdout.write(self.style.SUCCESS("Gemini API connection is working."))
        self.stdout.write("A live response was received successfully.")
