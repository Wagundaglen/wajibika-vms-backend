from django.contrib import admin
from .models import TrainingCourse, TrainingModule, TrainingAssignment, TrainingProgress, Certificate

@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']

@admin.register(TrainingModule)
class TrainingModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_active']
    list_filter = ['course', 'is_active']
    search_fields = ['title', 'content']

@admin.register(TrainingAssignment)
class TrainingAssignmentAdmin(admin.ModelAdmin):
    list_display = ['volunteer', 'course', 'assigned_by', 'assigned_date', 'due_date', 'status']
    list_filter = ['status', 'assigned_date', 'course']
    search_fields = ['volunteer__user__username', 'course__title']

@admin.register(TrainingProgress)
class TrainingProgressAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'module', 'started_at', 'completed_at', 'is_completed']
    list_filter = ['is_completed', 'started_at', 'completed_at']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'assignment', 'issued_date']
    list_filter = ['issued_date']
    search_fields = ['certificate_id', 'assignment__volunteer__user__username']