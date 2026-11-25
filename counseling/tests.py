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
