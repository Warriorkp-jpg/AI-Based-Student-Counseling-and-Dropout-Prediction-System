from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from students.models import FeedbackAnnouncement, FeedbackConversation, FeedbackMessage, StudentProfile
from users.models import User


@override_settings(GEMINI_API_KEY='')
class DashboardRoutingTests(TestCase):
    def test_teacher_sees_teacher_dashboard(self):
        teacher = User.objects.create_user(
            username='teacher1',
            password='secret123',
            role='teacher',
        )

        self.client.login(username='teacher1', password='secret123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher_dashboard.html')
        self.assertContains(response, 'Teacher portal')

    def test_student_without_profile_is_redirected_to_update_page(self):
        student = User.objects.create_user(
            username='student1',
            password='secret123',
            role='student',
        )

        self.client.login(username='student1', password='secret123')
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('update_profile'))

    def test_teacher_cannot_open_student_profile_form(self):
        teacher = User.objects.create_user(
            username='teacher2',
            password='secret123',
            role='teacher',
        )

        self.client.login(username='teacher2', password='secret123')
        response = self.client.get(reverse('update_profile'))

        self.assertRedirects(response, reverse('dashboard'))

    def test_student_with_profile_sees_student_dashboard(self):
        student = User.objects.create_user(
            username='student2',
            password='secret123',
            role='student',
        )
        StudentProfile.objects.create(
            user=student,
            cgpa=8.2,
            attendance=91,
            stress_level=3,
            annual_income=120000,
        )

        self.client.login(username='student2', password='secret123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_teacher_can_open_student_detail_page(self):
        teacher = User.objects.create_user(
            username='teacher3',
            password='secret123',
            role='teacher',
        )
        student = User.objects.create_user(
            username='student3',
            password='secret123',
            role='student',
        )
        profile = StudentProfile.objects.create(
            user=student,
            clg_name='K College',
            roll_no='42',
            cgpa=7.5,
            attendance=80,
            stress_level=5,
            annual_income=150000,
        )

        self.client.login(username='teacher3', password='secret123')
        response = self.client.get(reverse('student_detail', args=[profile.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_detail.html')
        self.assertContains(response, 'K College')

    def test_student_can_open_ai_feature_pages(self):
        student = User.objects.create_user(
            username='featurestudent',
            password='secret123',
            role='student',
        )
        StudentProfile.objects.create(
            user=student,
            cgpa=7.9,
            attendance=88,
            stress_level=4,
            annual_income=180000,
        )

        self.client.login(username='featurestudent', password='secret123')

        self.assertEqual(self.client.get(reverse('ai_tutor_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dropout_prediction_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_analysis_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('study_planner_dashboard')).status_code, 200)

    def test_student_sees_dummy_course_curriculum(self):
        student = User.objects.create_user(username='course_student', password='secret123', role='student')
        StudentProfile.objects.create(user=student, course='cse', year=2)

        self.client.login(username='course_student', password='secret123')
        response = self.client.get(reverse('course_hub'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Structures')

    def test_teacher_can_send_private_feedback_and_student_can_reply(self):
        teacher = User.objects.create_user(username='feedback_teacher', password='secret123', role='teacher')
        student = User.objects.create_user(username='feedback_student', password='secret123', role='student')
        profile = StudentProfile.objects.create(user=student, course='cse', year=2)

        self.client.login(username='feedback_teacher', password='secret123')
        response = self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'start_conversation',
            'student_id': profile.id,
        })
        conversation = FeedbackConversation.objects.get(teacher=teacher, student=student)
        self.assertRedirects(response, f"{reverse('teacher_feedback_hub')}?conversation={conversation.id}")

        self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'message',
            'conversation_id': conversation.id,
            'body': 'Please revise the first two data structure modules this week.',
        })
        self.assertTrue(FeedbackMessage.objects.filter(conversation=conversation, sender=teacher).exists())

        self.client.login(username='feedback_student', password='secret123')
        self.client.post(reverse('student_feedback_inbox'), {
            'conversation_id': conversation.id,
            'body': 'Thank you, I will complete them by Friday.',
        })
        self.assertTrue(FeedbackMessage.objects.filter(conversation=conversation, sender=student).exists())

    def test_student_only_sees_feedback_for_own_course(self):
        teacher = User.objects.create_user(username='announce_teacher', password='secret123', role='teacher')
        student = User.objects.create_user(username='announce_student', password='secret123', role='student')
        StudentProfile.objects.create(user=student, course='cse', year=1)
        FeedbackAnnouncement.objects.create(teacher=teacher, title='CSE note', body='CSE feedback', target_course='cse')
        FeedbackAnnouncement.objects.create(teacher=teacher, title='MBA note', body='MBA feedback', target_course='mba')

        self.client.login(username='announce_student', password='secret123')
        response = self.client.get(reverse('student_feedback_inbox'))

        self.assertContains(response, 'CSE note')
        self.assertNotContains(response, 'MBA note')


class FeedbackSecurityTests(TestCase):
    def setUp(self):
        from django.test import Client

        self.client = Client(enforce_csrf_checks=True)
        self.teacher = User.objects.create_user(
            username='secure_teacher', password='secret123', role='teacher'
        )
        self.other_teacher = User.objects.create_user(
            username='other_teacher', password='secret123', role='teacher'
        )
        self.student = User.objects.create_user(
            username='secure_student', password='secret123', role='student'
        )
        self.other_student = User.objects.create_user(
            username='other_student', password='secret123', role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student, course='cse', year=2
        )
        StudentProfile.objects.create(
            user=self.other_student, course='mba', year=1
        )
        self.conversation = FeedbackConversation.objects.create(
            teacher=self.teacher, student=self.student
        )
        self.other_conversation = FeedbackConversation.objects.create(
            teacher=self.other_teacher, student=self.other_student
        )

    def _csrf_headers(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        token = response.cookies['csrftoken'].value
        return {'HTTP_X_CSRFTOKEN': token}

    def test_teacher_private_message_requires_csrf_token(self):
        self.client.login(username='secure_teacher', password='secret123')
        response = self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'message',
            'conversation_id': self.conversation.id,
            'body': 'A message without a CSRF token',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(FeedbackMessage.objects.exists())

    def test_teacher_can_send_private_message_with_csrf_token(self):
        self.client.login(username='secure_teacher', password='secret123')
        url = reverse('teacher_feedback_hub') + f'?conversation={self.conversation.id}'
        headers = self._csrf_headers(url)
        response = self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'message',
            'conversation_id': self.conversation.id,
            'body': 'Please review the feedback notes.',
        }, **headers)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FeedbackMessage.objects.filter(
            conversation=self.conversation, sender=self.teacher
        ).exists())

    def test_student_can_reply_with_csrf_token(self):
        self.client.login(username='secure_student', password='secret123')
        url = reverse('student_feedback_inbox') + f'?conversation={self.conversation.id}'
        headers = self._csrf_headers(url)
        response = self.client.post(reverse('student_feedback_inbox'), {
            'conversation_id': self.conversation.id,
            'body': 'Thank you for the feedback.',
        }, **headers)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FeedbackMessage.objects.filter(
            conversation=self.conversation, sender=self.student
        ).exists())

    def test_teacher_cannot_read_another_teachers_conversation(self):
        self.client.login(username='secure_teacher', password='secret123')
        FeedbackMessage.objects.create(
            conversation=self.other_conversation,
            sender=self.other_teacher,
            body='Private message belonging to another teacher.',
        )
        response = self.client.get(
            reverse('teacher_feedback_hub') + f'?conversation={self.other_conversation.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private message belonging to another teacher.')

    def test_student_cannot_read_another_students_conversation(self):
        self.client.login(username='secure_student', password='secret123')
        FeedbackMessage.objects.create(
            conversation=self.other_conversation,
            sender=self.other_teacher,
            body='Private message belonging to another student.',
        )
        response = self.client.get(
            reverse('student_feedback_inbox') + f'?conversation={self.other_conversation.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private message belonging to another student.')

    def test_malformed_conversation_id_does_not_crash(self):
        self.client.login(username='secure_teacher', password='secret123')
        response = self.client.get(reverse('teacher_feedback_hub') + '?conversation=not-a-number')
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_open_teacher_feedback_hub(self):
        self.client.login(username='secure_student', password='secret123')
        response = self.client.get(reverse('teacher_feedback_hub'))
        self.assertRedirects(response, reverse('student_feedback_inbox'))

    def test_empty_or_oversized_message_is_not_saved(self):
        self.client.login(username='secure_teacher', password='secret123')
        url = reverse('teacher_feedback_hub') + f'?conversation={self.conversation.id}'
        headers = self._csrf_headers(url)

        self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'message',
            'conversation_id': self.conversation.id,
            'body': '   ',
        }, **headers)
        self.client.post(reverse('teacher_feedback_hub'), {
            'action': 'message',
            'conversation_id': self.conversation.id,
            'body': 'x' * 4001,
        }, **headers)

        self.assertFalse(FeedbackMessage.objects.exists())
