from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_verified', 'is_online', 'date_joined']
    list_filter = ['is_verified', 'is_online', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra', {'fields': ('avatar', 'bio', 'is_verified', 'otp_code', 'is_online', 'last_seen')}),
    )
