from django.test import TestCase, override_settings
from django.urls import reverse

from students.models import StudentProfile
from users.models import User


@override_settings(GEMINI_API_KEY='')
class AICounselingDashboardTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student_ai',
            password='secret123',
            role='student',
        )
        self.teacher = User.objects.create_user(
            username='teacher_ai',
            password='secret123',
            role='teacher',
        )
        StudentProfile.objects.create(
            user=self.student,
            cgpa=7.4,
            attendance=81,
            stress_level=5,
            financial_problem=False,
        )

    def test_student_dashboard_loads(self):
        self.client.login(username='student_ai', password='secret123')
        response = self.client.get(reverse('ai_counseling_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai_counseling_dashboard.html')
        self.assertContains(response, 'SyncAI Chatbot')

    def test_teacher_redirected_from_student_counseling_dashboard(self):
        self.client.login(username='teacher_ai', password='secret123')
        response = self.client.get(reverse('ai_counseling_dashboard'))

        self.assertRedirects(response, reverse('dashboard'))

    def test_post_message_adds_chat_history_to_session(self):
        self.client.login(username='student_ai', password='secret123')
        response = self.client.post(reverse('ai_counseling_dashboard'), {
            'message': 'Tell me about my risk',
        })

        self.assertRedirects(response, reverse('ai_counseling_dashboard'))
        self.assertIn('ai_counseling_chat', self.client.session)


class GeminiDiagnosticCommandTests(TestCase):
    @override_settings(GEMINI_API_KEY='test-key-not-used-for-network')
    def test_command_reports_success_for_a_mocked_live_response(self):
        from io import StringIO
        from types import SimpleNamespace
        from unittest.mock import patch

        from django.core.management import call_command

        output = StringIO()
        with patch(
            'counseling.management.commands.check_gemini_api._build_model'
        ) as build_model:
            build_model.return_value.generate_content.return_value = SimpleNamespace(
                text='GEMINI_CONNECTION_OK'
            )
            call_command('check_gemini_api', stdout=output)

        self.assertIn('Gemini API connection is working.', output.getvalue())
        build_model.return_value.generate_content.assert_called_once()

    @override_settings(GEMINI_API_KEY='')
    def test_command_refuses_to_run_without_a_configured_key(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command('check_gemini_api')
