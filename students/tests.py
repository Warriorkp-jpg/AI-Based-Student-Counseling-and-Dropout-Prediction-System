from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from students.models import StudentProfile
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
