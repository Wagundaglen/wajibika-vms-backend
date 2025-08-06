from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Volunteer

class VolunteerAdmin(UserAdmin):
    model = Volunteer
    list_display = ('username', 'email', 'phone', 'skills', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone', 'skills', 'role')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'skills', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'skills', 'role')}),
    )

admin.site.register(Volunteer, VolunteerAdmin)

