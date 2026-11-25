from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.action(description='Approve selected teacher registration requests')
def approve_teacher_requests(modeladmin, request, queryset):
    """Approval makes the selected teacher accounts eligible to sign in."""
    queryset.filter(role='teacher').update(teacher_approved=True, is_active=True)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'first_name', 'role', 'teacher_approved', 'is_active', 'is_staff')
    list_filter = ('role', 'teacher_approved', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = (approve_teacher_requests,)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Portal access', {'fields': ('role', 'teacher_approved')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Portal access', {'fields': ('role', 'teacher_approved')}),
    )
