from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assigned_to', 'due_date', 'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'assigned_to__username')
    ordering = ('-created_at',)

    # Allow status to be updated directly from the list view
    list_editable = ('status',)
