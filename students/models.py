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
    roll_no = models.CharField(max_length=10,blank=True, null= True)

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
        return self.user.username