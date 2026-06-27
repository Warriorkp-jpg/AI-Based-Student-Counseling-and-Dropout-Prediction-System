from django.urls import path
from .views import (
    ai_tutor_dashboard,
    dashboard,
    dropout_prediction_dashboard,
    student_analysis_dashboard,
    student_detail,
    study_planner_dashboard,
    update_profile,
)

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('update-profile/', update_profile, name='update_profile'),
    path('students/<int:student_id>/', student_detail, name='student_detail'),
    path('ai-tutor/', ai_tutor_dashboard, name='ai_tutor_dashboard'),
    path('dropout-prediction/', dropout_prediction_dashboard, name='dropout_prediction_dashboard'),
    path('student-analysis/', student_analysis_dashboard, name='student_analysis_dashboard'),
    path('study-planner/', study_planner_dashboard, name='study_planner_dashboard'),
    
]


