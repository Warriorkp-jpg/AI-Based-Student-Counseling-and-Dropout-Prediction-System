from django.test import TestCase
from django.urls import reverse

from students.models import StudentProfile
from .models import User


class RollNumberAuthenticationTests(TestCase):
    password = 'StrongPass123!'

    def register(self, **overrides):
        data = {
            'full_name': 'Alex Kumar',
            'roll_no': 'CSE-2026-001',
            'password': self.password,
            'role': 'student',
        }
        data.update(overrides)
        return self.client.post(reverse('register'), data)

    def test_students_with_the_same_name_can_register_with_different_roll_numbers(self):
        response = self.register(roll_no='CSE-2026-001')
        self.assertRedirects(response, reverse('login'))

        response = self.register(roll_no='CSE-2026-002')
        self.assertRedirects(response, reverse('login'))

        self.assertEqual(User.objects.filter(first_name='Alex Kumar', role='student').count(), 2)
        self.assertTrue(StudentProfile.objects.filter(roll_no='CSE-2026-001').exists())
        self.assertTrue(StudentProfile.objects.filter(roll_no='CSE-2026-002').exists())

    def test_student_logs_in_with_roll_number(self):
        self.register(roll_no='CSE-2026-003')

        response = self.client.post(reverse('login'), {
            'roll_no': 'cse-2026-003',
            'password': self.password,
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.session['_auth_user_id'], str(User.objects.get(username='CSE-2026-003').id))

    def test_duplicate_roll_number_is_rejected(self):
        self.register(roll_no='CSE-2026-004')
        response = self.register(full_name='Another Alex', roll_no='CSE-2026-004')

        self.assertRedirects(response, reverse('register'))
        self.assertEqual(User.objects.filter(username='CSE-2026-004').count(), 1)

    def test_teacher_request_cannot_login_until_admin_approves_it(self):
        response = self.register(
            full_name='Dr Priya Sharma',
            roll_no='STAFF-101',
            role='teacher',
        )
        self.assertRedirects(response, reverse('login'))

        teacher = User.objects.get(username='STAFF-101')
        self.assertFalse(teacher.is_active)
        self.assertFalse(teacher.teacher_approved)

        response = self.client.post(reverse('login'), {
            'roll_no': 'STAFF-101',
            'password': self.password,
        })
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        teacher.is_active = True
        teacher.teacher_approved = True
        teacher.save(update_fields=['is_active', 'teacher_approved'])
        response = self.client.post(reverse('login'), {
            'roll_no': 'STAFF-101',
            'password': self.password,
        })
        self.assertRedirects(response, reverse('dashboard'))
