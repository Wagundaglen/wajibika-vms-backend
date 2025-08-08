from django.contrib import admin
from .models import TrainingModule, TrainingProgress


@admin.register(TrainingModule)
class TrainingModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)


@admin.register(TrainingProgress)
class TrainingProgressAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'module', 'status', 'completed_at')
    list_filter = ('status', 'completed_at')
    search_fields = ('volunteer__username', 'module__title')
    ordering = ('-completed_at',)

    # Allow status updates directly from list view
    list_editable = ('status',)
