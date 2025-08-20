from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from .models import (
    FeedbackCategory, Feedback, FeedbackResponse, 
    FeedbackVote, FeedbackAnalytics
)

@admin.register(FeedbackCategory)
class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'feedback_count', 'created_at']
    search_fields = ['name', 'description']
    
    def feedback_count(self, obj):
        return obj.feedback_set.count()
    feedback_count.short_description = "Feedback Count"

class FeedbackResponseInline(admin.TabularInline):
    model = FeedbackResponse
    extra = 1
    fields = ['responder', 'message', 'is_internal']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user_info', 'feedback_type', 'sentiment', 
        'priority', 'status', 'assigned_to', 'created_at', 'response_count'
    ]
    list_filter = [
        'status', 'priority', 'sentiment', 'feedback_type', 
        'category', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'user__username', 
        'user__email', 'anonymous_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    inlines = [FeedbackResponseInline]
    
    fieldsets = (
        ('Feedback Information', {
            'fields': (
                'user', 'is_anonymous', 'anonymous_name', 'anonymous_email',
                'category', 'feedback_type', 'title', 'message', 'sentiment'
            )
        }),
        ('Status & Assignment', {
            'fields': ('priority', 'status', 'assigned_to', 'resolution_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '<b>{}</b><br>{}',
                obj.user.get_full_name() or obj.user.username,
                obj.user.role
            )
        elif obj.is_anonymous and obj.anonymous_name:
            return format_html(
                '<b>Anonymous: {}</b>',
                obj.anonymous_name
            )
        return "Anonymous"
    user_info.short_description = "Submitted By"
    
    def response_count(self, obj):
        return obj.responses.count()
    response_count.short_description = "Responses"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'category', 'assigned_to'
        ).annotate(response_count=Count('responses'))
    
    actions = ['mark_as_resolved', 'assign_to_me', 'export_as_csv']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.filter(status__in=['open', 'in_progress']).update(
            status='resolved',
            resolved_at=timezone.now()
        )
        self.message_user(
            request, 
            f"{updated} feedback entries marked as resolved.", 
            level='success'
        )
    mark_as_resolved.short_description = "Mark selected as resolved"
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(
            request, 
            f"{updated} feedback entries assigned to you.", 
            level='success'
        )
    assign_to_me.short_description = "Assign selected to me"
    
    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="feedback_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'User', 'Type', 'Sentiment', 'Priority', 
            'Status', 'Created', 'Message'
        ])
        
        for feedback in queryset:
            writer.writerow([
                feedback.title,
                feedback.user.get_full_name() if feedback.user else 'Anonymous',
                feedback.get_feedback_type_display(),
                feedback.get_sentiment_display(),
                feedback.get_priority_display(),
                feedback.get_status_display(),
                feedback.created_at.strftime('%Y-%m-%d %H:%M'),
                feedback.message
            ])
        
        return response
    export_as_csv.short_description = "Export selected as CSV"

@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ['feedback_title', 'responder', 'message_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['feedback__title', 'message', 'responder__username']
    
    def feedback_title(self, obj):
        return obj.feedback.title
    feedback_title.short_description = "Feedback"
    
    def message_preview(self, obj):
        return (obj.message[:50] + '...') if len(obj.message) > 50 else obj.message
    message_preview.short_description = "Message"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('feedback', 'responder')

@admin.register(FeedbackVote)
class FeedbackVoteAdmin(admin.ModelAdmin):
    list_display = ['feedback_title', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['feedback__title', 'user__username']
    
    def feedback_title(self, obj):
        return obj.feedback.title
    feedback_title.short_description = "Feedback"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('feedback', 'user')

@admin.register(FeedbackAnalytics)
class FeedbackAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_feedback', 'positive_count', 'neutral_count', 
        'negative_count', 'resolved_count', 'avg_resolution_time'
    ]
    list_filter = ['date']
    readonly_fields = ['date', 'total_feedback', 'positive_count', 'neutral_count', 
                     'negative_count', 'resolved_count', 'avg_resolution_time']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False