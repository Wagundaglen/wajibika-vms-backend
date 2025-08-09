from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'to_user',
        'from_user_display',
        'status',
        'created_at',
        'anonymous',
    )
    list_filter = ('status', 'anonymous', 'created_at')
    search_fields = ('message', 'to_user__username', 'from_user__username')
    list_editable = ('status',)
    ordering = ('-created_at',)  # Newest first
    date_hierarchy = 'created_at'  # Calendar navigation on the right

    def from_user_display(self, obj):
        return obj.from_user if obj.from_user else "Anonymous"
    from_user_display.short_description = "From User"
