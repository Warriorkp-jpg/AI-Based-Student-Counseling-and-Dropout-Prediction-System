from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    # Teacher accounts are created as requests and must be approved by an admin.
    teacher_approved = models.BooleanField(default=False)

    @property
    def display_name(self):
        """Use the saved name in the UI while keeping username as the login ID."""
        return self.get_full_name().strip() or self.username
