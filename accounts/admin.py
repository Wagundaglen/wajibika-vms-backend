from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Volunteer

@admin.register(Volunteer)
class VolunteerAdmin(UserAdmin):
    model = Volunteer

    def group_names(self, obj):
        groups = obj.groups.all()
        return ", ".join([group.name for group in groups]) if groups else "No groups"
    group_names.short_description = "Groups"

    list_display = ('username', 'email', 'phone', 'skills', 'role', 'group_names', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone', 'skills', 'role')
    list_filter = ('role', 'is_staff', 'is_superuser')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined')
    list_per_page = 20  # Show 20 users per page

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'skills', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'skills', 'role')}),
    )

    filter_horizontal = ('groups', 'user_permissions',)
