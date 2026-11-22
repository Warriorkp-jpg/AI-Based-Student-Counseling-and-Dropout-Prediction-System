from django.contrib import admin
from .models import FeedbackAnnouncement, FeedbackConversation, FeedbackMessage, StudentProfile
# Register your models here.


admin.site.register(StudentProfile)
admin.site.register(FeedbackAnnouncement)
admin.site.register(FeedbackConversation)
admin.site.register(FeedbackMessage)
