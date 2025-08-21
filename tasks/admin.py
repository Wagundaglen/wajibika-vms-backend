from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Task, TaskCategory, TimeEntry

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {}  # No slug field in this model

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'status', 'acceptance_status', 'priority', 'due_date', 'created_by', 'created_at')
    list_filter = ('status', 'acceptance_status', 'priority', 'category', 'created_by')
    search_fields = ('title', 'description', 'assigned_to__username', 'assigned_to__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Assignment Details', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'start_time', 'end_date', 'end_time', 'due_date', 'location')
        }),
        ('Requirements', {
            'fields': ('skills_required', 'estimated_hours')
        }),
        ('Status Tracking', {
            'fields': ('status', 'acceptance_status', 'priority', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to', 'created_by', 'category')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            kwargs["queryset"] = User.objects.filter(role__in=['Volunteer', 'Coordinator'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['mark_as_completed', 'mark_as_in_progress']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status__in=['Pending', 'In Progress']).update(
            status='Completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f"{updated} tasks marked as completed.")
    mark_as_completed.short_description = "Mark selected tasks as completed"
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.filter(status='Pending').update(status='In Progress')
        self.message_user(request, f"{updated} tasks marked as in progress.")
    mark_as_in_progress.short_description = "Mark selected tasks as in progress"

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'task', 'date', 'hours', 'approved', 'approved_by', 'created_at')
    list_filter = ('approved', 'date', 'volunteer')
    search_fields = ('volunteer__username', 'task__title', 'description')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Time Entry Details', {
            'fields': ('volunteer', 'task', 'date', 'hours', 'description')
        }),
        ('Approval', {
            'fields': ('approved', 'approved_by')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer', 'task')
    
    actions = ['approve_entries', 'reject_entries']
    
    def approve_entries(self, request, queryset):
        updated = queryset.filter(approved=False).update(
            approved=True,
            approved_by=request.user
        )
        self.message_user(request, f"{updated} time entries approved.")
    approve_entries.short_description = "Approve selected time entries"
    
    def reject_entries(self, request, queryset):
        count, _ = queryset.filter(approved=False).delete()
        self.message_user(request, f"{count} time entries rejected and deleted.")
    reject_entries.short_description = "Reject and delete selected time entries"