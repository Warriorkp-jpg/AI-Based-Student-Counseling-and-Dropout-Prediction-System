from django.urls import path
from .views import ai_counseling_dashboard

urlpatterns = [
    path('ai_counseling_dashboard/',ai_counseling_dashboard,name='ai_counseling_dashboard'),
]
