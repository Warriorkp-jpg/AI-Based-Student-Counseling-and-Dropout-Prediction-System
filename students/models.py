from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class StudentProfile(models.Model):

    COURSE_CHOICES = [
        ('cse', 'Computer Science'),
        ('aiml', 'AI & Machine Learning'),
        ('mech', 'Mechanical Engineering'),
        ('bba', 'BBA'),
        ('mba', 'MBA'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='students/', blank=True, null=True)

    clg_name = models.CharField(max_length=100,blank=True, null= True)
    # A roll number identifies a student account and must not be shared.
    roll_no = models.CharField(max_length=30, unique=True, blank=True, null=True)

    course = models.CharField(max_length=30, choices=COURSE_CHOICES ,null= True , blank= True)
    year = models.IntegerField(blank=True, null= True)

    cgpa = models.FloatField(default=0)
    attendance = models.FloatField(default=0)

    stress_level = models.FloatField(default=0)
    problems = models.TextField(blank=True, null= True)
    
    financial_problem = models.BooleanField(default=False)
    annual_income = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.display_name


class FeedbackConversation(models.Model):
    """One private feedback thread between a teacher and a student."""
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_feedback_conversations',
        limit_choices_to={'role__in': ['teacher', 'admin']},
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_feedback_conversations',
        limit_choices_to={'role': 'student'},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'student'],
                name='unique_teacher_student_feedback_conversation',
            ),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.teacher.display_name} and {self.student.display_name}"


class FeedbackMessage(models.Model):
    """A single professional message inside a private feedback conversation."""
    conversation = models.ForeignKey(
        FeedbackConversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.display_name}: {self.body[:40]}"


class FeedbackAnnouncement(models.Model):
    """A teacher announcement for all students or one selected course."""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_announcements')
    title = models.CharField(max_length=120)
    body = models.TextField()
    target_course = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
