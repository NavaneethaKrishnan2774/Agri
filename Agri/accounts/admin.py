from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("contact_number", "name", "role", "is_staff")
    search_fields = ("contact_number", "name")
