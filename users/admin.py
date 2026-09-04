from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "phone", "city", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone")
    ordering = ("username",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional", {"fields": ("phone", "address", "city", "postal_code")}),
    )
